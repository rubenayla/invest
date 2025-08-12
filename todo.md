- Could I gain better analysis with an AI such as yourself, claude, or gemini (free) something like that? Maybe includes news, more external data that's not easily accessible via api but requires google searches and iteration? I'm interested in this too.
  ✅ DONE: Claude Desktop integration complete with systematic screening + research tools

- commit
- Include more companies, not just the 30 biggest from the sp500
- Add other markets, not just usa
- Consider gold, bitcoin, etc. as alternatives to stocks, instructions for AI to consider waiting, like berkshire has sometimes done, to wait for better opportunities with treasuries, short-term bonds, etc.
- What about berkshire hathaway? 

## AI Integration Roadmap (Cost-Effective Alternatives)

### Phase 1: Claude Desktop (Current - FREE with subscription)
✅ Systematic screening tools
✅ Research and analysis tools  
✅ Portfolio construction tools
- Usage: Interactive analysis via Claude Desktop

### Phase 2: Multi-Model Support (Future - Cost Reduction)
- **Gemini Pro (Free tier)**: 
  - 15 requests/minute free
  - Web search capability built-in
  - Good for news research, sector analysis
  - Integration: `src/invest/ai/providers/gemini.py`

- **Local Ollama Models (100% Free)**:
  - Llama 3.1, Mistral, CodeLlama
  - Zero API costs, runs locally
  - Privacy: no data leaves your machine
  - Good for: basic analysis, report generation
  - Integration: `src/invest/ai/providers/ollama.py`

- **OpenAI GPT-4 (Backup)**:
  - More expensive but reliable
  - Good API documentation
  - Integration: `src/invest/ai/providers/openai.py`

### Phase 3: Smart Routing System
- Route queries to optimal AI based on:
  - Complexity (simple → local, complex → cloud)
  - Cost (free tier → Gemini/local, premium → Claude)
  - Capabilities (web search → Gemini, reasoning → Claude)
  
### Phase 4: Automation Options
- **Batch Analysis**: Run overnight with cheaper models
- **Scheduled Screening**: Weekly systematic screening
- **Alert System**: Monitor portfolio changes
- **API Integration**: For programmatic access

### Cost Comparison (Monthly estimates):
- Claude Desktop: $0 (with existing subscription)
- Gemini Pro: $0-15 (free tier + overage)
- Local Ollama: $0 (hardware requirements: 8GB+ RAM)
- OpenAI GPT-4: $20-100+ (depends on usage)

### Next Steps:
1. Test current Claude Desktop integration
2. Add Gemini provider for web research
3. Set up local Ollama for basic tasks
4. Implement smart routing logic




- Could we run our system with this set of stocks and etfs to invest, and let it decide what to buy in each period, and calculate the average return it would obtain from x to y? It should obviously not get data from the future of each decision, this is a test to see how it would have performed in the past.



---

- learn acgl

fixed? fix dcf model so it uses averages of years and gets trends in auto mode

use second method of comparative valuation

- Investigate Japanese situation (estanflacion ya no, precio bajo?)
- Argentina stocks, growth but might have fallen with Trump

## Check
- Argetina
- MITSY
- intersect of warren, sec.gov people, etc investments. people close to trump that hold stocks etc.
    - Dominari Holdings
    - American Bitcoin
    - Affinity Partners
    - WLF
- COINBASE:
    - Matches cathie wood, peter thiel, marc andreessen, david scaks, dan loeb, ...

- IBKR Market screener 2.0


- Update checklists to use check operating margin instead of gross
- Check these stocks: BIDU, CSCO, IBM, META, ORCL, PYPL, QCOM, SAP
- Study LOGI in more depth. Great fundamentals. I would pay twice its stock value
- Study skyworks in more depth
- Study steel dynamics. What's going to happen with steel demand? If it falls back down after all these investments, the stock will collapse.

- [ ] Create spreadsheet to calculate price according to assumptions in bad - medium - good scenarios.(https://youtu.be/H1gfAXvRoSM)
- [ ] gdi? P/E = 12 cuando es predecible y crece

- Valuation models
    - Graham
        - ![](readme/20230523133421.png)
    - Discounted Cash Flow (DCF)
    - Multiples
    - Dividend discount

## Copypaste to do one
Price:
Shares:

Checklist:
- Price/Gross Profit =  < 10
- Gross profit margin =  > .1
- Revenue grows 
- Gross profit grows 
- Shares outstanding 
- Equity
- Equity per share = $/share
- Time to pay debt: Long term liabilities / free cash flow =  /  =  < 5

### Estimate stock price
- Value = Equity + PE_estimated * Gross Profit = 
- Price per stock = Value / Shares = $/stock
- Current price: $/stock

---
EDGAR parsing? implement it?