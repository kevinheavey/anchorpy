from typing import Any, Callable, List, Dict
from sys import maxsize

from base58 import b58encode
from solana.message import Message, CompiledInstruction, MessageArgs, MessageHeader
from solana.transaction import Transaction, AccountMeta, SigPubkeyPair

from anchorpy.public_key import PublicKey
from anchorpy.program.context import split_args_and_context
from anchorpy.idl import IdlInstruction
from anchorpy.program.namespace.instruction import InstructionFn


class NewTransaction(Transaction):
    def __repr__(self):
        return f"Transaction{self.signatures=}, {self.instructions=}, {self.fee_payer=}, {self.recent_blockhash}>"

    def compile_message(self) -> Message:
        """Compile transaction data."""
        if self.nonce_info and self.instructions[0] != self.nonce_info.nonce_instruction:
            self.recent_blockhash = self.nonce_info.nonce
            self.instructions = [self.nonce_info.nonce_instruction] + self.instructions

        if not self.recent_blockhash:
            raise AttributeError("transaction recentBlockhash required")
        if len(self.instructions) < 1:
            raise AttributeError("no instructions provided")

        fee_payer = self.fee_payer
        if not fee_payer and len(self.signatures) > 0 and self.signatures[0].pubkey:
            # Use implicit fee payer
            fee_payer = self.signatures[0].pubkey

        if not fee_payer:
            raise AttributeError("transaction feePayer required")

        account_metas, program_ids = [], set()
        for instr in self.instructions:
            if not instr.program_id:
                raise AttributeError("invalid instruction:", instr)
            account_metas.extend(instr.keys)
            program_ids.add(str(instr.program_id))

        # Append programID account metas.
        for pg_id in program_ids:
            account_metas.append(AccountMeta(PublicKey(pg_id), False, False))

        # Sort. Prioritizing first by signer, then by writable and converting from set to list.
        account_metas.sort(key=lambda account: (not account.is_signer, not account.is_writable))

        # Cull duplicate accounts
        fee_payer_idx = maxsize
        seen: Dict[str, int] = dict()
        uniq_metas: List[AccountMeta] = []
        for sig in self.signatures:
            pubkey = str(sig.pubkey)
            if pubkey in seen:
                uniq_metas[seen[pubkey]].is_signer = True
            else:
                uniq_metas.append(AccountMeta(sig.pubkey, True, True))
                seen[pubkey] = len(uniq_metas) - 1
                if sig.pubkey == fee_payer:
                    fee_payer_idx = min(fee_payer_idx, seen[pubkey])

        for a_m in account_metas:
            pubkey = str(a_m.pubkey)
            if pubkey in seen:
                idx = seen[pubkey]
                uniq_metas[idx].is_writable = uniq_metas[idx].is_writable or a_m.is_writable
            else:
                uniq_metas.append(a_m)
                seen[pubkey] = len(uniq_metas) - 1
                if a_m.pubkey == fee_payer:
                    fee_payer_idx = min(fee_payer_idx, seen[pubkey])

        # Move fee payer to the front
        if fee_payer_idx == maxsize:
            uniq_metas = [AccountMeta(fee_payer, True, True)] + uniq_metas
        else:
            uniq_metas = (
                    [uniq_metas[fee_payer_idx]] + uniq_metas[:fee_payer_idx] + uniq_metas[fee_payer_idx + 1:]
            # noqa: E203
            )

        # Split out signing from nonsigning keys and count readonlys
        signed_keys: List[str] = []
        unsigned_keys: List[str] = []
        num_required_signatures = num_readonly_signed_accounts = num_readonly_unsigned_accounts = 0
        for a_m in uniq_metas:
            if a_m.is_signer:
                signed_keys.append(str(a_m.pubkey))
                num_required_signatures += 1
                num_readonly_signed_accounts += int(not a_m.is_writable)
            else:
                num_readonly_unsigned_accounts += int(not a_m.is_writable)
                unsigned_keys.append(str(a_m.pubkey))
        # Initialize signature array, if needed
        if not self.signatures:
            self.signatures = [SigPubkeyPair(pubkey=PublicKey(key), signature=None) for key in signed_keys]

        account_keys: List[str] = signed_keys + unsigned_keys
        account_indices: Dict[str, int] = {str(key): i for i, key in enumerate(account_keys)}
        compiled_instructions: List[CompiledInstruction] = [
            CompiledInstruction(
                accounts=[account_indices[str(a_m.pubkey)] for a_m in instr.keys],
                program_id_index=account_indices[str(instr.program_id)],
                data=b58encode(instr.data),
            )
            for instr in self.instructions
        ]

        return Message(
            MessageArgs(
                header=MessageHeader(
                    num_required_signatures=num_required_signatures,
                    num_readonly_signed_accounts=num_readonly_signed_accounts,
                    num_readonly_unsigned_accounts=num_readonly_unsigned_accounts,
                ),
                account_keys=account_keys,
                instructions=compiled_instructions,
                recent_blockhash=self.recent_blockhash,
            )
        )


TransactionFn = Callable[[Any], NewTransaction]


class TransactionNamespace(object):
    pass


class TransactionNamespaceFactory(object):
    @staticmethod
    def build(idl_ix: IdlInstruction, ix_fn: InstructionFn) -> TransactionFn:
        def tx_fn(*args: List[Any]) -> NewTransaction:
            args = list(args)
            new_args, ctx = split_args_and_context(idl_ix, args)
            tx = NewTransaction()
            if ctx.instructions:
                tx.add(*ctx.instructions)
            tx.add(ix_fn(*args))
            return tx

        return tx_fn
