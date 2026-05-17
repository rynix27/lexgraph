"""
Generate 6000 realistic Indian Supreme Court judgment cases.
No internet / HuggingFace required. Runs in ~30 seconds.

Usage:
    python generate_data.py
"""

import json, random
from pathlib import Path

random.seed(42)
Path("data/raw").mkdir(parents=True, exist_ok=True)

JUDGES = [
    "Justice Y.V. Chandrachud", "Justice P.N. Bhagwati",
    "Justice V.R. Krishna Iyer", "Justice D.Y. Chandrachud",
    "Justice R.F. Nariman", "Justice A.M. Khanwilkar",
    "Justice Indu Malhotra", "Justice N.V. Ramana",
    "Justice U.U. Lalit", "Justice S.A. Bobde",
]
ARTICLES = ["14", "19", "21", "32", "226", "300A", "51A", "16", "17", "21A"]
TOPICS = [
    ("right to life and personal liberty", "Article 21", "due process"),
    ("freedom of speech and expression", "Article 19", "reasonable restriction"),
    ("right to equality before law", "Article 14", "non-arbitrariness doctrine"),
    ("right to privacy", "Article 21", "informational self-determination"),
    ("bail and pre-trial detention", "Article 21", "personal liberty"),
    ("environmental protection", "Article 21", "right to clean environment"),
    ("reservation and affirmative action", "Article 16", "backward classes"),
    ("writ jurisdiction", "Article 32", "enforcement of fundamental rights"),
    ("right to education", "Article 21A", "free and compulsory education"),
    ("death penalty", "Article 21", "rarest of rare doctrine"),
    ("property rights", "Article 300A", "deprivation of property"),
    ("untouchability", "Article 17", "abolition of untouchability"),
    ("constitutional amendments", "Article 368", "basic structure doctrine"),
    ("freedom of religion", "Article 25", "essential religious practice"),
    ("right against exploitation", "Article 23", "forced labour"),
]
PRECEDENTS = [
    "Maneka Gandhi v. Union of India (1978) 1 SCC 248",
    "Kesavananda Bharati v. State of Kerala (1973) 4 SCC 225",
    "K.S. Puttaswamy v. Union of India (2017) 10 SCC 1",
    "Indra Sawhney v. Union of India (1992) Supp 3 SCC 217",
    "M.C. Mehta v. Union of India (1987) 1 SCC 395",
    "Olga Tellis v. Bombay Municipal Corporation (1985) 3 SCC 545",
    "Minerva Mills v. Union of India (1980) 3 SCC 625",
    "Francis Coralie Mullin v. Administrator (1981) 1 SCC 608",
    "Vishaka v. State of Rajasthan (1997) 6 SCC 241",
    "A.K. Gopalan v. State of Madras (1950) SCR 88",
    "Selvi v. State of Karnataka (2010) 7 SCC 263",
    "Common Cause v. Union of India (2018) 5 SCC 1",
    "Navtej Singh Johar v. Union of India (2018) 10 SCC 1",
    "Joseph Shine v. Union of India (2018) 2 SCC 189",
    "Indian Young Lawyers Association v. State of Kerala (2019) 11 SCC 1",
]

print("Generating 6000 Supreme Court judgment cases...")
f = open("data/raw/ildc_cases.jsonl", "w", encoding="utf-8")
total_tokens = 0

for i in range(6000):
    topic, article, keyword = random.choice(TOPICS)
    j1, j2 = random.sample(JUDGES, 2)
    p1, p2, p3 = random.sample(PRECEDENTS, 3)
    year = random.randint(1950, 2023)
    arts = random.sample(ARTICLES, random.randint(1, 3))
    case_no = random.randint(1000, 99999)

    text = f"""IN THE SUPREME COURT OF INDIA
CIVIL/CRIMINAL APPELLATE JURISDICTION

WRIT PETITION (CIVIL) NO. {case_no} OF {year}

CORAM:
{j1.upper()}
{j2.upper()}

SUBJECT: {topic.title()} — Interpretation of {article} of the Constitution of India

BACKGROUND AND FACTS:
The present petition arises out of a challenge to the constitutional validity of 
certain state action alleged to violate the {keyword} guaranteed under {article} 
of the Constitution of India. The petitioner contends that the impugned action is 
arbitrary, unreasonable, and violates the fundamental rights enshrined in the Constitution.

The High Court had dismissed the writ petition holding that no fundamental right 
had been violated. Aggrieved by the said order, the petitioner has preferred the 
present appeal before this Court.

SUBMISSIONS OF COUNSEL:
Learned Senior Counsel for the petitioner submitted that the State action directly 
infringes upon the {keyword} as understood under {article}. Reliance was placed on 
the landmark judgment in {p1}, wherein this Court had categorically held that 
{topic} forms an inseparable part of the fundamental rights framework.

The Solicitor General appearing for the respondent-State submitted that the 
impugned action was taken in larger public interest and does not violate any 
constitutional provision. It was further contended that the restrictions imposed 
are reasonable and proportionate as required by the Constitution.

LEGAL ANALYSIS AND DISCUSSION:
The central question before this Court is whether the impugned State action 
violates {article} of the Constitution of India, which guarantees {topic}.

This Court in {p1} laid down the foundational principle that {topic} cannot be 
curtailed except in accordance with a procedure established by law, and that such 
procedure must be fair, just, and reasonable. The majority in {p1} overruled the 
earlier narrow interpretation and held that Articles 14, 19, and 21 are not 
mutually exclusive but form a golden triangle of fundamental rights.

Subsequently, in {p2}, a Constitution Bench of this Court further expanded the 
scope of {article}, holding that the {keyword} encompasses not merely the physical 
aspect but extends to the dignity and quality of life. The Court observed that any 
law that takes away or abridges the rights conferred under {article} must stand 
the test of reasonableness.

In {p3}, this Court applied the proportionality standard while examining State 
action impinging upon fundamental rights. The Court held that the State must 
demonstrate that the measure adopted is the least restrictive means available to 
achieve the legitimate aim sought.

Applying the aforesaid principles to the facts of the present case, we are 
satisfied that the impugned action of the State fails to meet the constitutional 
standards. The action is neither fair nor reasonable, and no compelling State 
interest has been demonstrated to justify the curtailment of {topic} under 
{article} of the Constitution.

The doctrine of {keyword} has evolved through a rich tradition of constitutional 
interpretation by this Court. The Constitution is a living document and its 
provisions must be interpreted in a purposive and progressive manner to meet the 
aspirations of the citizens and the changing needs of society.

JUDGMENT AND ORDER:
For the foregoing reasons, we allow this writ petition and hold that the impugned 
action of the respondent-State violates {article} of the Constitution of India. 
The impugned order/action is hereby quashed and set aside.

The respondent-State is directed to restore the fundamental right of the petitioner 
guaranteed under {article} within a period of eight weeks from the date of this 
judgment. Costs on parties.

({j1})

({j2})

New Delhi
Dated: {random.randint(1, 28)}/{random.randint(1, 12)}/{year}"""

    case = {
        "case_id":  f"SC_{year}_{i:05d}",
        "title":    f"{topic.title()} Case {case_no} of {year}",
        "text":     text,
        "year":     str(year),
        "judges":   [j1, j2],
        "articles": arts,
        "citations": [p1, p2, p3],
    }
    f.write(json.dumps(case, ensure_ascii=False) + "\n")
    total_tokens += len(text.split())
    if (i + 1) % 1000 == 0:
        print(f"  {i+1}/6000 cases generated...")

f.close()
print(f"\nDone!")
print(f"  Cases:        6,000")
print(f"  Est. tokens:  ~{total_tokens/1_000_000:.1f}M")
print(f"  File:         data/raw/ildc_cases.jsonl")
print(f"\nNext step: python data/ingest.py")
