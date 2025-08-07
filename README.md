# 🌍 FundsRUS - Climate Tech Funding Intelligence Platform

![FundsRUS Logo](earth-sunrise-from-space-wallpaper-preview.jpg)

## Overview

FundsRUS is the most effective investor research tool for early-stage climate tech founders. We transform scattered funding data into actionable intelligence, helping founders identify the right investors with conviction signals, geographic focus, and stage-appropriate deal sizes. Our mission is to illuminate the funding landscape that's powering our planet's sustainable future.

## Features

- 🏦 **Investor-Centric Database**: Browse active climate tech investors with detailed profiles and deal history
- 🎯 **Advanced Fundraising Filters**: Lead investors only, geography targeting, and stage-relevant deal sizes
- 🔍 **Quick Company Search**: Instantly find who funded any company with "Who funded this company?" search
- 📊 **Conviction Signals**: Track lead vs. follow behavior to identify investors with strong conviction
- 🌍 **Geographic Intelligence**: Filter investors by North America, Europe, or global focus
- 💰 **Stage-Appropriate Targeting**: Deal size buckets aligned with funding stages (Seed, Series A, Series B+)
- 📈 **Interactive Profiles**: Click any investor to see their complete deal history and investment patterns
- 🌱 **Climate Focus**: Specialized tracking for climate tech and sustainability startups

## Tech Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas
- **Data Storage**: JSON
- **Styling**: Custom CSS with gradient branding

## Quick Start

### Prerequisites
- Python 3.7+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/fundsrus.git
cd fundsrus
```

2. Install dependencies:
```bash
pip install streamlit pandas
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

## Data Structure

The platform processes funding data with the following fields:
- Company Name
- Funding Date
- Amount & Currency
- Funding Stage
- Lead Investor(s)
- Other Investors
- Climate Vertical
- Company Description
- Source URL

## Usage

### For Fundraising Founders:
1. **Quick Research**: Use "Who funded this company?" to instantly find investors for competitors
2. **Target Lead Investors**: Check "Lead Investors Only" to focus on investors who actually write lead checks
3. **Geographic Targeting**: Filter by your target geography (North America, Europe, etc.)
4. **Stage-Appropriate Search**: Use deal size buckets to find investors active in your funding stage
5. **Deep Dive**: Click any investor to see their complete deal history and investment patterns
6. **Conviction Analysis**: Review lead deal counts to identify investors with strong conviction signals

### For Investors & Analysts:
1. **Market Intelligence**: Browse the complete investor database with advanced filtering
2. **Competitive Analysis**: Track peer investor activity and investment patterns
3. **Deal Flow**: Monitor funding activity across climate verticals and stages

## Business Model

- **Basic**: Individual users - $29/month
- **Professional**: Investment teams - $99/month  
- **Enterprise**: Institutions with API access - Custom pricing

## Future Work

The goal is to make this the most effective investor research tool for early-stage climate tech founders.

1. **Identify the Partner:** Use advanced NLP to extract the specific partner at the VC firm who led the deal from the source articles. This is the ultimate actionable insight.
2. **Integrate LinkedIn/Socials:** Add links to the VC firm's and partner's LinkedIn profiles to facilitate research for warm introductions.
3. **"Investor Has a Thesis In..." Alerts:** Allow founders to set up alerts for when an investor on their target list funds a new company in their specific vertical, signaling an active investment thesis.
4. **Full Automation Pipeline:** Implement the full RSS → AI Classifier → AI Extractor → Database pipeline to ensure the data is always up-to-date.

## Contributing

We welcome contributions! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or partnerships, reach out to us at [your-email@domain.com]

---

**FundsRUS** - *Illuminating the path to a sustainable future* 🌱
