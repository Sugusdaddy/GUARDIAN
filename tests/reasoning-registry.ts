import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { ReasoningRegistry } from "../target/types/reasoning_registry";
import { expect } from "chai";
import { createHash } from "crypto";

describe("reasoning-registry", () => {
  // Configure the client to use the devnet cluster.
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.ReasoningRegistry as Program<ReasoningRegistry>;
  
  // Test data
  const threatId = new anchor.BN(1);
  const reasoningText = "Analysis: This token shows classic rug pull indicators. " +
    "Mint authority is still enabled, allowing unlimited minting. " +
    "Top 5 wallets hold 95% of supply. " +
    "Liquidity is extremely low ($500). " +
    "Recommendation: BLOCK this token and alert community.";
  
  // Create hash of reasoning
  const reasoningHash = createHash("sha256")
    .update(reasoningText)
    .digest();

  let reasoningCommitPda: anchor.web3.PublicKey;
  let reasoningCommitBump: number;

  before(async () => {
    // Derive PDA for reasoning commit
    [reasoningCommitPda, reasoningCommitBump] = anchor.web3.PublicKey.findProgramAddressSync(
      [
        Buffer.from("reasoning"),
        provider.wallet.publicKey.toBuffer(),
        threatId.toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    );
  });

  it("Commits reasoning hash on-chain", async () => {
    const tx = await program.methods
      .commitReasoning(
        provider.wallet.publicKey,
        Array.from(reasoningHash),
        threatId,
        { warn: {} } // ActionType::Warn
      )
      .accounts({
        reasoningCommit: reasoningCommitPda,
        authority: provider.wallet.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Commit transaction:", tx);

    // Fetch the account and verify
    const account = await program.account.reasoningCommit.fetch(reasoningCommitPda);
    
    expect(account.agentId.toString()).to.equal(provider.wallet.publicKey.toString());
    expect(account.threatId.toNumber()).to.equal(1);
    expect(account.revealed).to.be.false;
    expect(Buffer.from(account.reasoningHash)).to.deep.equal(reasoningHash);
  });

  it("Reveals reasoning and verifies hash", async () => {
    const tx = await program.methods
      .revealReasoning(reasoningText)
      .accounts({
        reasoningCommit: reasoningCommitPda,
        agentId: provider.wallet.publicKey,
        authority: provider.wallet.publicKey,
      })
      .rpc();

    console.log("Reveal transaction:", tx);

    // Fetch and verify
    const account = await program.account.reasoningCommit.fetch(reasoningCommitPda);
    
    expect(account.revealed).to.be.true;
    expect(account.reasoningText).to.equal(reasoningText);
    expect(account.revealTimestamp).to.not.be.null;
  });

  it("Verifies reasoning integrity", async () => {
    const isValid = await program.methods
      .verifyReasoning()
      .accounts({
        reasoningCommit: reasoningCommitPda,
      })
      .view();

    expect(isValid).to.be.true;
    console.log("Reasoning verified successfully!");
  });

  it("Prevents double reveal", async () => {
    try {
      await program.methods
        .revealReasoning("Different text that shouldn't work")
        .accounts({
          reasoningCommit: reasoningCommitPda,
          agentId: provider.wallet.publicKey,
          authority: provider.wallet.publicKey,
        })
        .rpc();
      
      expect.fail("Should have thrown AlreadyRevealed error");
    } catch (err) {
      expect(err.message).to.include("AlreadyRevealed");
    }
  });
});
