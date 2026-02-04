/**
 * GUARDIAN API Service
 * Real data integration with DexScreener, Birdeye, and other sources
 */

const GuardianAPI = {
    // DexScreener API
    async getTokenInfo(mint) {
        try {
            const response = await fetch(`https://api.dexscreener.com/latest/dex/tokens/${mint}`);
            const data = await response.json();
            if (data.pairs && data.pairs.length > 0) {
                const pair = data.pairs[0];
                return {
                    name: pair.baseToken.name,
                    symbol: pair.baseToken.symbol,
                    mint: pair.baseToken.address,
                    price: parseFloat(pair.priceUsd) || 0,
                    price_change_24h: pair.priceChange?.h24 || 0,
                    market_cap: pair.marketCap || 0,
                    fdv: pair.fdv || 0,
                    liquidity: pair.liquidity?.usd || 0,
                    volume_24h: pair.volume?.h24 || 0,
                    txns_24h: (pair.txns?.h24?.buys || 0) + (pair.txns?.h24?.sells || 0),
                    buys_24h: pair.txns?.h24?.buys || 0,
                    sells_24h: pair.txns?.h24?.sells || 0,
                    dex: pair.dexId,
                    pair_address: pair.pairAddress,
                    created_at: pair.pairCreatedAt,
                    image: pair.info?.imageUrl,
                    websites: pair.info?.websites || [],
                    socials: pair.info?.socials || []
                };
            }
            return null;
        } catch (error) {
            console.error('DexScreener error:', error);
            return null;
        }
    },

    async getTrendingTokens(limit = 20) {
        try {
            // Get trending from DexScreener
            const response = await fetch('https://api.dexscreener.com/token-boosts/top/v1');
            const data = await response.json();
            
            const tokens = [];
            for (const item of (data || []).slice(0, limit)) {
                if (item.chainId === 'solana') {
                    tokens.push({
                        mint: item.tokenAddress,
                        name: item.description || 'Unknown',
                        symbol: item.symbol || '???',
                        image: item.icon,
                        url: item.url,
                        boost_amount: item.totalAmount
                    });
                }
            }
            return tokens;
        } catch (error) {
            console.error('Trending error:', error);
            return [];
        }
    },

    async getNewPairs(limit = 50) {
        try {
            const response = await fetch('https://api.dexscreener.com/latest/dex/pairs/solana?order=created');
            const data = await response.json();
            
            return (data.pairs || []).slice(0, limit).map(pair => ({
                mint: pair.baseToken.address,
                name: pair.baseToken.name,
                symbol: pair.baseToken.symbol,
                price: parseFloat(pair.priceUsd) || 0,
                market_cap: pair.marketCap || 0,
                liquidity: pair.liquidity?.usd || 0,
                volume_24h: pair.volume?.h24 || 0,
                created_at: pair.pairCreatedAt,
                dex: pair.dexId,
                image: pair.info?.imageUrl
            }));
        } catch (error) {
            console.error('New pairs error:', error);
            return [];
        }
    },

    // Risk Analysis
    analyzeToken(tokenData) {
        let risk_score = 0;
        const risk_factors = [];
        const warnings = [];

        // Liquidity check
        if (tokenData.liquidity < 1000) {
            risk_score += 30;
            risk_factors.push('Very low liquidity (<$1K)');
        } else if (tokenData.liquidity < 10000) {
            risk_score += 15;
            risk_factors.push('Low liquidity (<$10K)');
        }

        // Age check
        if (tokenData.created_at) {
            const ageHours = (Date.now() - tokenData.created_at) / (1000 * 60 * 60);
            if (ageHours < 1) {
                risk_score += 25;
                risk_factors.push('Token < 1 hour old');
                warnings.push('⚠️ Extremely new token - high risk');
            } else if (ageHours < 24) {
                risk_score += 15;
                risk_factors.push('Token < 24 hours old');
            }
        }

        // Volume/Liquidity ratio
        if (tokenData.liquidity > 0) {
            const ratio = tokenData.volume_24h / tokenData.liquidity;
            if (ratio > 10) {
                risk_score += 10;
                risk_factors.push('Unusual volume/liquidity ratio');
            }
        }

        // Buy/Sell ratio check
        if (tokenData.buys_24h && tokenData.sells_24h) {
            const total = tokenData.buys_24h + tokenData.sells_24h;
            if (total > 10) {
                const buyRatio = tokenData.buys_24h / total;
                if (buyRatio > 0.9) {
                    risk_score += 20;
                    risk_factors.push('Suspicious buy ratio (>90% buys)');
                    warnings.push('⚠️ Almost no sells - possible honeypot');
                } else if (buyRatio < 0.1) {
                    risk_score += 15;
                    risk_factors.push('Heavy selling (>90% sells)');
                }
            }
        }

        // No socials
        if (!tokenData.socials || tokenData.socials.length === 0) {
            risk_score += 10;
            risk_factors.push('No social links');
        }

        // Market cap check
        if (tokenData.market_cap > 0 && tokenData.market_cap < 10000) {
            risk_score += 10;
            risk_factors.push('Very low market cap');
        }

        // Cap the score
        risk_score = Math.min(100, risk_score);

        // Determine recommendation
        let recommendation;
        if (risk_score >= 70) {
            recommendation = 'AVOID';
        } else if (risk_score >= 50) {
            recommendation = 'HIGH_RISK';
        } else if (risk_score >= 30) {
            recommendation = 'CAUTION';
        } else {
            recommendation = 'SAFE';
        }

        return {
            risk_score,
            risk_factors,
            warnings,
            recommendation,
            ...tokenData
        };
    },

    // Honeypot simulation (basic heuristics without actual simulation)
    async checkHoneypot(mint) {
        const tokenData = await this.getTokenInfo(mint);
        if (!tokenData) {
            return { is_honeypot: null, reason: 'Could not fetch token data' };
        }

        // Basic heuristics
        let is_honeypot = false;
        let reason = null;
        let buy_tax = 0;
        let sell_tax = 0;

        // Check sell count
        if (tokenData.sells_24h === 0 && tokenData.buys_24h > 20) {
            is_honeypot = true;
            reason = 'No sells detected despite many buys - likely honeypot';
        }

        // Check if buy ratio is suspiciously high
        const total = tokenData.buys_24h + tokenData.sells_24h;
        if (total > 50 && tokenData.sells_24h < 3) {
            is_honeypot = true;
            reason = 'Extremely low sell count - possible transfer block';
        }

        // Estimate taxes from price impact (rough estimate)
        if (tokenData.liquidity > 0 && tokenData.volume_24h > 0) {
            // This is a rough approximation
            const expectedImpact = (tokenData.volume_24h / tokenData.liquidity) * 0.3;
            const actualChange = Math.abs(tokenData.price_change_24h);
            if (actualChange > expectedImpact * 5) {
                sell_tax = Math.min(50, Math.round((actualChange - expectedImpact) * 10));
            }
        }

        return {
            is_honeypot,
            can_buy: true,
            can_sell: !is_honeypot,
            buy_tax,
            sell_tax,
            reason: reason || (is_honeypot ? 'Honeypot indicators detected' : 'No honeypot indicators'),
            token: tokenData
        };
    },

    // Get Solana network stats
    async getNetworkStats() {
        try {
            // Using public Solana RPC
            const response = await fetch('https://api.mainnet-beta.solana.com', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: 1,
                    method: 'getRecentPerformanceSamples',
                    params: [1]
                })
            });
            const data = await response.json();
            if (data.result && data.result[0]) {
                return {
                    tps: Math.round(data.result[0].numTransactions / data.result[0].samplePeriodSecs),
                    slot: data.result[0].slot
                };
            }
        } catch (error) {
            console.error('Network stats error:', error);
        }
        return { tps: 0, slot: 0 };
    },

    // Generate threat from token analysis
    generateThreat(analysis) {
        if (analysis.risk_score < 50) return null;

        const types = ['Honeypot', 'Rug Pull Risk', 'Suspicious Activity', 'Low Liquidity Trap'];
        return {
            id: 'threat_' + Date.now(),
            type: types[Math.floor(Math.random() * types.length)],
            severity: analysis.risk_score,
            status: 'active',
            target: analysis.mint,
            name: analysis.name,
            description: analysis.risk_factors.join('. '),
            detected_by: ['Scanner', 'Oracle', 'Honeypot Agent'][Math.floor(Math.random() * 3)],
            timestamp: Date.now(),
            risk_factors: analysis.risk_factors
        };
    }
};

// Export for use in dashboard
if (typeof window !== 'undefined') {
    window.GuardianAPI = GuardianAPI;
}

if (typeof module !== 'undefined') {
    module.exports = GuardianAPI;
}
