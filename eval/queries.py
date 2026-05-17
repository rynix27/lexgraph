"""10 benchmark queries for LexGraph — designed to maximise GraphRAG advantage."""

QUERIES = [
    {
        "id": "q01",
        "query": "Which judges have most consistently expanded the scope of Article 21 rights, and which landmark cases established those precedents?",
        "ground_truth": "Justice P.N. Bhagwati and Justice V.R. Krishna Iyer were prominent in expanding Article 21. Key cases include Maneka Gandhi v. Union of India (1978) and Francis Coralie Mullin v. Administrator (1981).",
    },
    {
        "id": "q02",
        "query": "How has the Supreme Court interpretation of the right to privacy under Article 21 evolved from the 1950s to the Puttaswamy judgment?",
        "ground_truth": "Privacy was not recognized initially (M.P. Sharma 1954, Kharak Singh 1963). K.S. Puttaswamy v. Union of India (2017) nine-judge bench unanimously held privacy is a fundamental right under Article 21.",
    },
    {
        "id": "q03",
        "query": "What is the basic structure doctrine and which cases have applied it to strike down constitutional amendments?",
        "ground_truth": "Basic structure doctrine established in Kesavananda Bharati v. State of Kerala (1973). Applied in Minerva Mills v. Union of India (1980) to strike down clauses of the 42nd Amendment.",
    },
    {
        "id": "q04",
        "query": "Which acts have been challenged most frequently under Article 14 right to equality in the Supreme Court?",
        "ground_truth": "Frequently challenged acts include the Prevention of Money Laundering Act and Armed Forces Special Powers Act. Article 14 challenges invoke non-arbitrariness established in E.P. Royappa v. State of Tamil Nadu (1974).",
    },
    {
        "id": "q05",
        "query": "What remedies has the Supreme Court granted in PIL cases involving environmental protection under Article 21?",
        "ground_truth": "The Court granted structural injunctions, appointed commissioners, ordered cleanup funds in M.C. Mehta cases, shut down industries, and created monitoring committees.",
    },
    {
        "id": "q06",
        "query": "Which prior judgments did Justice Y.V. Chandrachud cite when ruling on Article 21 cases and what principles did those judgments establish?",
        "ground_truth": "Justice Y.V. Chandrachud contributed to Maneka Gandhi (1978). He cited A.K. Gopalan v. State of Madras (1950) to distinguish and expand procedural due process requirements under Article 21.",
    },
    {
        "id": "q07",
        "query": "Trace the citation chain from Maneka Gandhi v. Union of India to cases decided after 2010 that relied on it to expand personal liberty rights.",
        "ground_truth": "Maneka Gandhi (1978) established that Article 21 requires fair just and reasonable procedure. Post-2010 cases include Selvi v. State of Karnataka (2010), Aruna Shanbaug (2011), and Common Cause v. Union of India (2018).",
    },
    {
        "id": "q08",
        "query": "Which Supreme Court judges authored the most judgments interpreting both Article 19 and Article 21 together and what doctrine emerged?",
        "ground_truth": "Justices P.N. Bhagwati and V.R. Krishna Iyer authored multiple judgments treating Articles 19 and 21 together, building the golden triangle doctrine linking Articles 14, 19, and 21.",
    },
    {
        "id": "q09",
        "query": "What is the chain of precedents that led the Supreme Court to recognise the right to livelihood as part of Article 21?",
        "ground_truth": "The chain: Francis Coralie Mullin (1981) then Olga Tellis v. Bombay Municipal Corporation (1985) then Unni Krishnan v. State of AP (1993). Olga Tellis held right to livelihood is part of right to life.",
    },
    {
        "id": "q10",
        "query": "Which constitutional bench decisions on reservation policy cite Indra Sawhney and how did judges interpret the 50 percent ceiling rule?",
        "ground_truth": "Indra Sawhney v. Union of India (1992) established 50 percent ceiling. Cases citing it include M. Nagaraj (2006), Jarnail Singh (2018), and Maratha reservation cases (2021) which reaffirmed the cap.",
    },
]
