module.exports = function handler(req, res) {
  res.setHeader('Vary', 'Accept');
  res.setHeader('Content-Type', 'text/markdown; charset=utf-8');
  
  // Clean the URL path
  const path = req.url.split('?')[0];

  if (path === '/' || path === '/index.md' || path === '/api/markdown') {
    res.status(200).send(`# LegalLens AI\n\nLegalLens AI is an Enterprise Compliance & Operations Assistant that uses a LangGraph-driven Evidence Decision Engine to actively resolve outdated, conflicting, or unauthorized information.\n\n## Key Features\n- **Structure-Aware Chunking:** Parses logical document boundaries.\n- **RBAC Meta-filtering:** Database-level role-based access control.\n- **Pre-LLM Precedence:** Resolves version and date conflicts before they hit the LLM.\n- **Hybrid RRF Search:** Combines dense semantic and sparse BM25 search.\n- **LangGraph State Machine:** Bounds LLM responses to prevent hallucination.\n\nFor documentation, see our [llms.txt](/llms.txt).`);
  } else {
    res.status(404).send(`# 404 Not Found\n\nThe requested resource could not be found.\n\nIf you are an AI agent looking for documentation or capabilities, please refer to:\n- [llms.txt](/llms.txt) for agentic usage instructions.\n- [Sitemap](/sitemap.xml) for a full list of indexable pages.\n- [MCP](/.well-known/mcp) for our Model Context Protocol definitions.`);
  }
}
