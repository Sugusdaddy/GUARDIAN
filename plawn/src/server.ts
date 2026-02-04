import express from "express";
import cors from "cors";
import { launchToken, uploadImage, getTokens, verifyMoltbookPost } from "./api";
import { db } from "./db";

const app = express();
app.use(cors());
app.use(express.json({ limit: "50mb" }));

// Health check
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "plawn", version: "1.0.0" });
});

// Upload image to IPFS
app.post("/api/upload", async (req, res) => {
  try {
    const { image, name } = req.body;
    
    if (!image) {
      return res.status(400).json({ error: "Image is required (base64 or URL)" });
    }

    const result = await uploadImage(image, name);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Launch token
app.post("/api/launch", async (req, res) => {
  try {
    const { moltbook_key, post_id } = req.body;

    if (!moltbook_key || !post_id) {
      return res.status(400).json({ 
        error: "Missing required fields",
        required: ["moltbook_key", "post_id"]
      });
    }

    // Verify Moltbook post and extract token config
    const postData = await verifyMoltbookPost(moltbook_key, post_id);
    
    if (!postData.success || !postData.config || !postData.agent) {
      return res.status(400).json({ error: postData.error, errors: postData.errors });
    }

    const { agent, config } = postData;

    // Check rate limit (1 per week)
    const lastLaunch = db.getLastLaunchByAgent(agent);
    if (lastLaunch) {
      const weekMs = 7 * 24 * 60 * 60 * 1000;
      const timeSince = Date.now() - new Date(lastLaunch.timestamp).getTime();
      if (timeSince < weekMs) {
        const daysLeft = Math.ceil((weekMs - timeSince) / (24 * 60 * 60 * 1000));
        return res.status(429).json({ 
          error: `Rate limit: 1 token per week`,
          hint: `Wait ${daysLeft} days before launching again`
        });
      }
    }

    // Check if ticker already used
    if (db.getTokenBySymbol(config.symbol)) {
      return res.status(400).json({ 
        error: "Ticker already launched",
        hint: "Choose a different symbol"
      });
    }

    // Check if post already used
    if (db.getTokenByPostId(post_id)) {
      return res.status(400).json({ 
        error: "Post already used for a launch",
        hint: "Create a new post"
      });
    }

    // Launch the token on pump.fun
    const result = await launchToken(config, agent, post_id);

    if (result.success && result.mint) {
      // Save to database
      db.addToken({
        id: result.mint,
        agent: agent,
        name: config.name,
        symbol: config.symbol,
        description: config.description,
        image: config.image,
        wallet: config.wallet,
        mint: result.mint,
        signature: result.signature || "",
        postId: post_id,
        postUrl: `https://www.moltbook.com/post/${post_id}`,
        pumpUrl: `https://pump.fun/${result.mint}`,
        timestamp: new Date().toISOString(),
      });

      res.json({
        success: true,
        agent: agent,
        post_id,
        post_url: `https://www.moltbook.com/post/${post_id}`,
        token_address: result.mint,
        tx_hash: result.signature,
        pump_url: `https://pump.fun/${result.mint}`,
        rewards: {
          agent_share: "80%",
          platform_share: "20%",
          agent_wallet: config.wallet
        }
      });
    } else {
      res.status(500).json({ 
        error: "Token launch failed",
        details: result.error 
      });
    }
  } catch (error: any) {
    console.error("Launch error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Get all launched tokens
app.get("/api/tokens", (_req, res) => {
  const tokens = db.getTokens();
  res.json({ success: true, tokens, count: tokens.length });
});

// Serve static files
app.use(express.static("public"));

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 PLAWN server running on port ${PORT}`);
  console.log(`   Health: http://localhost:${PORT}/api/health`);
});
