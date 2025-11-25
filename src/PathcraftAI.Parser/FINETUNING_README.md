# POE Expert Fine-tuning Guide

This guide explains how to collect Q&A data and fine-tune GPT-3.5 for Path of Exile expertise.

## Prerequisites

```bash
pip install openai praw  # Optional: for Reddit API
```

## Step 1: Set up API Keys

### OpenAI API Key (Required)
```bash
export OPENAI_API_KEY=sk-your-key-here
```

Get your key from: https://platform.openai.com/api-keys

### Reddit API (Optional - improves data quality)
```bash
export REDDIT_CLIENT_ID=your_client_id
export REDDIT_CLIENT_SECRET=your_secret
export REDDIT_USER_AGENT=PathcraftAI:v1.0
```

Get credentials from: https://www.reddit.com/prefs/apps

## Step 2: Collect Q&A Data

Run the data collection script:

```bash
python poe_qa_collector.py
```

This will:
- Collect 3,000 Q&A from Reddit (mock data if no API key)
- Collect 2,000 Q&A from POE Wiki (mock data)
- Collect 2,000 Q&A from POE Forum (mock data)
- Collect 2,000 Q&A from DC Inside (mock Korean data)
- Collect 1,000 Q&A from YouTube (mock data)
- Generate 5,000 template-based Q&A (high quality)

**Total: 15,000 Q&A pairs**

Output files:
- `data/qa_dataset/raw_qa_pairs.json` - Raw collected data
- `data/qa_dataset/finetuning_dataset.jsonl` - Formatted for OpenAI

## Step 3: Fine-tune GPT-3.5

Run the fine-tuning script:

```bash
python openai_finetuning.py
```

This will:
1. Validate the dataset (check format, count examples)
2. Upload to OpenAI (creates a file ID)
3. Create fine-tuning job (starts training)
4. Wait for completion (1-2 hours)

**Estimated Cost:**
- 15,000 examples × ~3 epochs = ~45,000 training steps
- Cost: ~$120 USD (as of 2025, prices may vary)

## Step 4: Use Your Fine-tuned Model

Once training completes, you'll get a model ID like:
```
ft:gpt-3.5-turbo:pathcraftai:poe-expert-v1:abc123
```

Use it in your application:

```python
import openai

response = openai.ChatCompletion.create(
    model="ft:gpt-3.5-turbo:pathcraftai:poe-expert-v1:abc123",
    messages=[
        {"role": "system", "content": "You are an expert Path of Exile assistant."},
        {"role": "user", "content": "What is the best league starter for 3.27?"}
    ]
)

print(response.choices[0].message.content)
```

## Data Sources

### Current Implementation (Mock Data)

All crawlers currently return mock data for development/testing:
- Reddit: 3 sample Q&A repeated
- Wiki: 5 sample Q&A about game mechanics
- Forum: 3 sample Q&A about builds
- DC Inside: 4 Korean Q&A samples
- YouTube: 3 sample build Q&A
- Templates: 5,000 generated from knowledge templates

### Future Real Data Collection

To implement real data collection, you'll need to:

1. **Reddit** (`reddit_qa_crawler.py`):
   - Install praw: `pip install praw`
   - Set up Reddit API credentials
   - Uncomment real scraping logic

2. **POE Wiki** (`wiki_qa_crawler.py`):
   - Install BeautifulSoup: `pip install beautifulsoup4 requests`
   - Implement wiki page scraping
   - Parse structured POE wiki content

3. **POE Forum** (`forum_qa_crawler.py`):
   - Implement web scraping for pathofexile.com/forum
   - Handle authentication if needed
   - Extract question/answer pairs from threads

4. **DC Inside** (`dcinside_qa_crawler.py`):
   - Handle DC Inside anti-bot measures
   - Parse Korean text properly
   - Extract Q&A from gallery posts

5. **YouTube** (`youtube_qa_crawler.py`):
   - Use YouTube Data API v3
   - Extract comments from POE videos
   - Filter Q&A patterns from comments

### Template-based Generation

High-quality Q&A pairs are generated from knowledge templates in `qa_template_generator.py`:

Categories:
- Build basics (archetypes, ascendancies, budget)
- Game mechanics (damage types, defenses, ailments)
- Crafting (methods, costs, item levels)
- Atlas strategies (farming, profitability)
- Leveling (progression, efficiency)

**Advantage:** Templates ensure factually correct, well-structured data.

## Quality Improvements

### Data Filtering

The `clean_and_format()` function filters:
- Minimum question length: 10 characters
- Minimum answer length: 20 characters
- Invalid entries (missing Q or A)

### Data Augmentation

To reach 10,000+ examples with current mock data:
- Mock data is duplicated to reach target counts
- Template generator creates diverse combinations
- Mix of English and Korean content

### Future Improvements

1. **Web Scraping**: Implement real crawlers for all sources
2. **Data Validation**: Use LLM to validate Q&A relevance and accuracy
3. **Deduplication**: Remove duplicate or near-duplicate Q&A
4. **Multilingual**: Add more Korean content from Korean POE communities
5. **Version-specific**: Tag Q&A with POE league version (3.27, 3.26, etc.)

## Monitoring Fine-tuning

Check training progress:

```bash
# List all fine-tuning jobs
openai api fine_tunes.list

# Check specific job status
openai api fine_tunes.get -i <job_id>

# Cancel a job
openai api fine_tunes.cancel -i <job_id>
```

## Troubleshooting

### "Dataset validation failed"
- Check JSONL format (one JSON object per line)
- Ensure each example has exactly 3 messages (system, user, assistant)
- Verify no empty questions or answers

### "Upload failed"
- Check your OpenAI API key is valid
- Ensure you have sufficient API credits
- Check file size (max 512 MB)

### "Fine-tuning failed"
- Review error message in job status
- Common issues: dataset too small (<50 examples), format errors
- Check OpenAI status page for service issues

## Cost Optimization

To reduce costs:
- Start with 1,000-2,000 examples for testing
- Use 1 epoch instead of 3
- Filter only high-quality Q&A pairs

## Next Steps

After fine-tuning:
1. Test the model with sample questions
2. Compare responses to base GPT-3.5
3. Integrate into PathcraftAI UI
4. Implement Expert Tier ($5/month) in PRD

## References

- [OpenAI Fine-tuning Guide](https://platform.openai.com/docs/guides/fine-tuning)
- [OpenAI Pricing](https://openai.com/pricing)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [POE Wiki](https://www.poewiki.net/)
