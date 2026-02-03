import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { ThreatIntelligence } from "../target/types/threat_intelligence";
import { expect } from "chai";
import { createHash } from "crypto";

describe("threat-intelligence", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.ThreatIntelligence as Program<ThreatIntelligence>;

  let threatCounterPda: anchor.web3.PublicKey;
  let threatPda: anchor.web3.PublicKey;

  const evidenceHash = createHash("sha256")
    .update("Evidence: Contract analysis shows mint authority enabled")
    .digest();

  const maliciousAddress = anchor.web3.Keypair.generate().publicKey;

  before(async () => {
    // Derive threat counter PDA
    [threatCounterPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("threat_counter")],
      program.programId
    );
  });

  it("Initializes threat counter", async () => {
    try {
      const tx = await program.methods
        .initializeThreatCounter()
        .accounts({
          threatCounter: threatCounterPda,
          authority: provider.wallet.publicKey,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .rpc();

      console.log("Initialize counter tx:", tx);
    } catch (err) {
      // Counter might already exist
      console.log("Counter may already be initialized");
    }

    const counter = await program.account.threatCounter.fetch(threatCounterPda);
    console.log("Current threat count:", counter.count.toNumber());
  });

  it("Registers a new threat", async () => {
    const counter = await program.account.threatCounter.fetch(threatCounterPda);
    const threatId = counter.count;

    // Derive threat PDA
    [threatPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("threat"), threatId.toArrayLike(Buffer, "le", 8)],
      program.programId
    );

    const tx = await program.methods
      .registerThreat(
        { rugPull: {} }, // ThreatType::RugPull
        85, // severity
        maliciousAddress, // target address
        "Detected rug pull: Mint authority enabled, 95% held by 5 wallets",
        Array.from(evidenceHash)
      )
      .accounts({
        threat: threatPda,
        threatCounter: threatCounterPda,
        authority: provider.wallet.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Register threat tx:", tx);

    // Verify
    const threat = await program.account.threat.fetch(threatPda);
    expect(threat.threatId.toNumber()).to.equal(threatId.toNumber());
    expect(threat.severity).to.equal(85);
    expect(threat.status).to.deep.equal({ active: {} });
  });

  it("Confirms a threat (simulating multi-agent consensus)", async () => {
    // In production, this would be called by a different agent
    const tx = await program.methods
      .confirmThreat()
      .accounts({
        threat: threatPda,
        authority: provider.wallet.publicKey,
      })
      .rpc();

    console.log("Confirm threat tx:", tx);

    const threat = await program.account.threat.fetch(threatPda);
    expect(threat.confirmedBy.length).to.be.greaterThan(0);
  });

  it("Adds address to watchlist", async () => {
    const [watchlistPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("watchlist"), maliciousAddress.toBuffer()],
      program.programId
    );

    const tx = await program.methods
      .addToWatchlist(
        maliciousAddress,
        "Rug pull operator - extracted 500 SOL",
        new anchor.BN(0) // linked threat ID
      )
      .accounts({
        watchlistEntry: watchlistPda,
        authority: provider.wallet.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Add to watchlist tx:", tx);

    const entry = await program.account.watchlistEntry.fetch(watchlistPda);
    expect(entry.active).to.be.true;
    expect(entry.address.toString()).to.equal(maliciousAddress.toString());
  });

  it("Checks watchlist status", async () => {
    const [watchlistPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("watchlist"), maliciousAddress.toBuffer()],
      program.programId
    );

    const isWatchlisted = await program.methods
      .checkWatchlist()
      .accounts({
        watchlistEntry: watchlistPda,
      })
      .view();

    expect(isWatchlisted).to.be.true;
    console.log("Address is watchlisted:", isWatchlisted);
  });

  it("Updates threat status to neutralized", async () => {
    const tx = await program.methods
      .updateThreatStatus({ neutralized: {} })
      .accounts({
        threat: threatPda,
        authority: provider.wallet.publicKey,
      })
      .rpc();

    console.log("Update status tx:", tx);

    const threat = await program.account.threat.fetch(threatPda);
    expect(threat.status).to.deep.equal({ neutralized: {} });
  });
});
