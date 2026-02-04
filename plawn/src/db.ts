import * as fs from "fs";
import * as path from "path";

const DB_PATH = path.join(process.cwd(), "data", "tokens.json");

interface Token {
  id: string;
  agent: string;
  name: string;
  symbol: string;
  description: string;
  image: string;
  wallet: string;
  mint: string;
  signature: string;
  postId: string;
  postUrl: string;
  pumpUrl: string;
  timestamp: string;
}

interface Database {
  tokens: Token[];
}

function ensureDir() {
  const dir = path.dirname(DB_PATH);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function load(): Database {
  ensureDir();
  if (fs.existsSync(DB_PATH)) {
    return JSON.parse(fs.readFileSync(DB_PATH, "utf-8"));
  }
  return { tokens: [] };
}

function save(data: Database) {
  ensureDir();
  fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 2));
}

export const db = {
  getTokens(): Token[] {
    return load().tokens;
  },

  addToken(token: Token) {
    const data = load();
    data.tokens.unshift(token);
    save(data);
  },

  getTokenBySymbol(symbol: string): Token | undefined {
    return load().tokens.find(t => t.symbol.toLowerCase() === symbol.toLowerCase());
  },

  getTokenByPostId(postId: string): Token | undefined {
    return load().tokens.find(t => t.postId === postId);
  },

  getLastLaunchByAgent(agent: string): Token | undefined {
    return load().tokens.find(t => t.agent === agent);
  },

  getTokensByAgent(agent: string): Token[] {
    return load().tokens.filter(t => t.agent === agent);
  },
};
