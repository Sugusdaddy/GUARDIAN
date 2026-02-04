import { Connection, Keypair, VersionedTransaction } from "@solana/web3.js";
import bs58 from "bs58";
import FormData from "form-data";

const PUMPDEV_API = "https://pumpdev.io";
const PUMP_IPFS_API = "https://pump.fun/api/ipfs";
const MOLTBOOK_API = "https://www.moltbook.com/api/v1";
const SOLANA_RPC = process.env.SOLANA_RPC_URL || "https://api.mainnet-beta.solana.com";
const PLAWN_PRIVATE_KEY = process.env.PLAWN_PRIVATE_KEY || "";

const JITO_ENDPOINTS = [
  "https://mainnet.block-engine.jito.wtf",
  "https://amsterdam.mainnet.block-engine.jito.wtf",
  "https://frankfurt.mainnet.block-engine.jito.wtf",
  "https://ny.mainnet.block-engine.jito.wtf",
  "https://tokyo.mainnet.block-engine.jito.wtf",
];

export interface TokenConfig {
  name: string;
  symbol: string;
  description: string;
  image: string;
  wallet: string;
}

export interface LaunchResult {
  success: boolean;
  mint?: string;
  signature?: string;
  error?: string;
}

// Upload image to pump.fun IPFS
export async function uploadImage(image: string, name?: string): Promise<{ success: boolean; url?: string; error?: string }> {
  try {
    const formData = new FormData();
    
    // Check if it's a URL or base64
    if (image.startsWith("http")) {
      // Fetch and re-upload
      const response = await fetch(image);
      const buffer = Buffer.from(await response.arrayBuffer());
      formData.append("file", buffer, { filename: `${name || "image"}.jpg`, contentType: "image/jpeg" });
    } else {
      // Base64 data
      const base64Data = image.replace(/^data:image\/\w+;base64,/, "");
      const buffer = Buffer.from(base64Data, "base64");
      formData.append("file", buffer, { filename: `${name || "image"}.jpg`, contentType: "image/jpeg" });
    }

    formData.append("name", name || "token-image");
    formData.append("symbol", "IMG");
    formData.append("description", "PLAWN token image");
    formData.append("showName", "false");

    const response = await fetch(PUMP_IPFS_API, {
      method: "POST",
      body: formData as any,
    });

    const result = await response.json() as { metadataUri?: string };
    
    if (result.metadataUri) {
      // Extract image URL from metadata
      const metaResponse = await fetch(result.metadataUri);
      const metadata = await metaResponse.json() as { image?: string };
      return { success: true, url: metadata.image || result.metadataUri };
    }

    return { success: true, url: result.metadataUri };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}

// Verify Moltbook post and extract token config
export async function verifyMoltbookPost(apiKey: string, postId: string): Promise<{
  success: boolean;
  agent?: string;
  config?: TokenConfig;
  error?: string;
  errors?: string[];
}> {
  try {
    // Get agent info
    const agentRes = await fetch(`${MOLTBOOK_API}/agents/me`, {
      headers: { "Authorization": `Bearer ${apiKey}` }
    });
    
    if (!agentRes.ok) {
      return { success: false, error: "Invalid Moltbook API key" };
    }

    const agentData = await agentRes.json() as { agent?: { name?: string } };
    const agentName = agentData.agent?.name;

    if (!agentName) {
      return { success: false, error: "Could not get agent info" };
    }

    // Get post
    const postRes = await fetch(`${MOLTBOOK_API}/posts/${postId}`, {
      headers: { "Authorization": `Bearer ${apiKey}` }
    });

    if (!postRes.ok) {
      return { success: false, error: "Post not found" };
    }

    const postData = await postRes.json() as { post?: { content: string; authorName: string } };
    const post = postData.post;

    if (!post) {
      return { success: false, error: "Post not found" };
    }

    // Verify post belongs to this agent
    if (post.authorName !== agentName) {
      return { success: false, error: "Post does not belong to this agent" };
    }

    // Check for !plawn trigger
    if (!post.content.includes("!plawn")) {
      return { success: false, error: "Post must contain !plawn trigger" };
    }

    // Extract JSON from code block
    const jsonMatch = post.content.match(/```json\s*([\s\S]*?)```/);
    if (!jsonMatch) {
      return { 
        success: false, 
        error: "No valid JSON found",
        errors: ["JSON must be in a code block (```json ... ```)"]
      };
    }

    let config: TokenConfig;
    try {
      config = JSON.parse(jsonMatch[1].trim());
    } catch {
      return { success: false, error: "Invalid JSON format" };
    }

    // Validate required fields
    const errors: string[] = [];
    
    if (!config.name || config.name.length > 50) {
      errors.push("Name is required (max 50 chars)");
    }
    if (!config.symbol || config.symbol.length > 10 || !/^[A-Za-z0-9]+$/.test(config.symbol)) {
      errors.push("Symbol is required (max 10 chars, letters/numbers only)");
    }
    if (!config.description || config.description.length > 500) {
      errors.push("Description is required (max 500 chars)");
    }
    if (!config.wallet || !/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(config.wallet)) {
      errors.push("Valid Solana wallet address is required");
    }
    if (!config.image) {
      errors.push("Image URL is required");
    }

    if (errors.length > 0) {
      return { success: false, error: "Invalid token configuration", errors };
    }

    // Append PLAWN suffix to description
    config.description = `${config.description}\n\n{LAUNCHED WITH PLAWN}`;

    return { success: true, agent: agentName, config };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}

// Launch token on pump.fun via PumpDev API
export async function launchToken(config: TokenConfig, agent: string, postId: string): Promise<LaunchResult> {
  try {
    if (!PLAWN_PRIVATE_KEY) {
      throw new Error("PLAWN_PRIVATE_KEY not configured");
    }

    const keypair = Keypair.fromSecretKey(bs58.decode(PLAWN_PRIVATE_KEY));
    const connection = new Connection(SOLANA_RPC, "confirmed");

    console.log(`🚀 Launching token ${config.symbol} for ${agent}...`);

    // Step 1: Upload metadata to pump.fun IPFS
    const formData = new FormData();
    
    // Fetch image and add to form
    const imageResponse = await fetch(config.image);
    const imageBuffer = Buffer.from(await imageResponse.arrayBuffer());
    formData.append("file", imageBuffer, { filename: "token.jpg", contentType: "image/jpeg" });
    formData.append("name", config.name);
    formData.append("symbol", config.symbol.toUpperCase());
    formData.append("description", config.description);
    formData.append("website", `https://www.moltbook.com/post/${postId}`);
    formData.append("showName", "true");

    const metaRes = await fetch(PUMP_IPFS_API, {
      method: "POST",
      body: formData as any,
    });

    const metaData = await metaRes.json() as { metadataUri?: string };
    const metadataUri = metaData.metadataUri;

    if (!metadataUri) {
      throw new Error("Failed to upload metadata");
    }

    console.log(`📝 Metadata URI: ${metadataUri}`);

    // Step 2: Create token via PumpDev API
    const createRes = await fetch(`${PUMPDEV_API}/api/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        publicKey: keypair.publicKey.toBase58(),
        name: config.name,
        symbol: config.symbol.toUpperCase(),
        uri: metadataUri,
        buyAmountSol: 0.01, // Small initial buy
        slippage: 30,
        jitoTip: 0.01,
        priorityFee: 0.001,
      }),
    });

    if (!createRes.ok) {
      const errorData = await createRes.json() as { error?: string };
      throw new Error(errorData.error || "PumpDev API error");
    }

    const createData = await createRes.json() as { 
      mint: string; 
      mintSecretKey: string; 
      transactions: Array<{ transaction: string; signers: string[] }> 
    };
    const mintAddress = createData.mint;
    const mintKeypair = Keypair.fromSecretKey(bs58.decode(createData.mintSecretKey));

    console.log(`🪙 Mint address: ${mintAddress}`);

    // Step 3: Sign transactions
    const signedTxs = createData.transactions.map((txInfo) => {
      const tx = VersionedTransaction.deserialize(bs58.decode(txInfo.transaction));
      const signers = txInfo.signers.includes("mint")
        ? [keypair, mintKeypair]
        : [keypair];
      tx.sign(signers);
      return bs58.encode(tx.serialize());
    });

    // Step 4: Send via Jito
    const bundleResult = await sendJitoBundle(signedTxs);

    if (!bundleResult.success) {
      // Fallback: send directly
      console.log("⚠️ Jito failed, sending directly...");
      for (const signedTx of signedTxs) {
        const tx = VersionedTransaction.deserialize(bs58.decode(signedTx));
        const sig = await connection.sendTransaction(tx, { skipPreflight: true });
        await connection.confirmTransaction(sig, "confirmed");
      }
    }

    console.log(`✅ Token launched: https://pump.fun/${mintAddress}`);

    return {
      success: true,
      mint: mintAddress,
      signature: bundleResult.bundleId || "direct",
    };
  } catch (error: any) {
    console.error("❌ Launch failed:", error.message);
    return { success: false, error: error.message };
  }
}

// Send Jito bundle
async function sendJitoBundle(signedTxs: string[]): Promise<{ success: boolean; bundleId?: string }> {
  for (const endpoint of JITO_ENDPOINTS) {
    try {
      const res = await fetch(`${endpoint}/api/v1/bundles`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "sendBundle",
          params: [signedTxs],
        }),
      });

      const data = await res.json() as { result?: string };
      if (data.result) {
        console.log(`✅ Jito bundle sent: ${data.result}`);
        return { success: true, bundleId: data.result };
      }
    } catch {
      continue;
    }
  }
  return { success: false };
}

// Get all tokens
export function getTokens() {
  const { db } = require("./db");
  return db.getTokens();
}
