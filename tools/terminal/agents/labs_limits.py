"""Product Checker action limits. Every number here was copied from the cited regulation text (fetched Oct 30, 2026).
labs.py re-fetches each source weekly and checks that the quoted text ("must") is still there; if a source changes or
goes away, that rule is published with status "needs review" and the browser checker stops using its numbers.
Units: heavy metals µg/g (= ppm), mycotoxins µg/kg (= ppb)."""
LIMITS=[
 dict(id="ca_metals",state="CA",panel="heavy_metals",title="California heavy metals action levels",cite="Cal. Code Regs. tit. 4, § 15723(c)",
      url="https://www.law.cornell.edu/regulations/california/4-CCR-15723",
      must=["Cadmium 0.2 0.5 Lead 0.5 0.5 Arsenic 0.2 1.5 Mercury 0.1 3.0"],unit="µg/g",
      inhalable=dict(cadmium=0.2,lead=0.5,arsenic=0.2,mercury=0.1),non_inhalable=dict(cadmium=0.5,lead=0.5,arsenic=1.5,mercury=3.0)),
 dict(id="ca_myco",state="CA",panel="mycotoxins",title="California mycotoxin limits",cite="Cal. Code Regs. tit. 4, § 15721(c)",
      url="https://www.law.cornell.edu/regulations/california/4-CCR-15721",
      must=["Total of aflatoxin B1, B2, G1, and G2 does not exceed 20","Ochratoxin A does not exceed 20"],unit="µg/kg",
      all=dict(total_aflatoxins=20,ochratoxin_a=20)),
 dict(id="ca_micro",state="CA",panel="microbials",title="California microbial limits",cite="Cal. Code Regs. tit. 4, § 15720(c)-(d)",
      url="https://www.law.cornell.edu/regulations/california/4-CCR-15720",
      must=["Shiga toxin-producing Escherichia coli is not detected in 1 gram","Salmonella spp. is not detected in 1 gram","A. fumigatus, A. flavus, A. niger, and A. terreus are not detected in 1 gram"],
      text="Not detected in 1 g: STEC E. coli and Salmonella (all products); pathogenic Aspergillus fumigatus, flavus, niger, terreus (inhalable products)."),
 dict(id="ca_drywt",state="CA",panel="potency",title="California dry-weight formula",cite="Cal. Code Regs. tit. 4, § 15724(c)(1)(A)",
      url="https://www.law.cornell.edu/regulations/california/4-CCR-15724",
      must=["Dry-weight percent cannabinoid = wet-weight percent cannabinoid / (1- percent moisture / 100)"],
      text="Dry-weight % = wet-weight % / (1 - moisture % / 100)."),
 dict(id="us_total_thc",state="US",panel="potency",title="USDA hemp total THC formula and 0.3% dry-weight limit",cite="7 CFR § 990.1",
      url="https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/title-7?part=990&section=990.1",
      must=["Total THC = (0.877 x THCA) + THC]","total delta-9 tetrahydrocannabinol content concentration level on a dry weight basis"],
      all=dict(total_thc_pct_dry=0.3),text="Total THC = 0.877 × THCA + Δ9-THC; hemp must test at or under 0.3% on a dry-weight basis (after measurement uncertainty)."),
 dict(id="us_dec11",state="US",panel="potency",title="New federal hemp definition (Dec 11, 2026)",cite="P.L. 119-37 Div. B § 781, as delayed by P.L. 119-103 (CRS IF13136)",
      url="https://www.congress.gov/crs-product/IF13136",
      must=["0.4 milligrams","December 11, 2026"],
      all=dict(mg_total_thc_per_container=0.4,total_thc_pct_dry=0.3),effective="2026-12-11",
      hand_checked="2026-10-30",  # congress.gov blocks scripted reads; text read by hand (CRS IF13136, updated 9/28/2026)
      text="From Dec 11, 2026: final hemp products over 0.4 mg combined total THC (and similar cannabinoids) per container are no longer hemp; total THC including THCA must be 0.3% or less by dry weight. From Nov 12, 2026: cannabinoids that the plant cannot naturally make are excluded."),
 # Michigan: CRA "Sampling and Testing Technical Guidance for Marijuana Products" (PDF). Its URL carries a ?rev= that
 # changes on each revision, so the weekly run finds the current link on the Scientific Section page ("find") and
 # checks the quoted text in the PDF; a new version (or changed numbers) makes these rows "needs review".
 dict(id="mi_metals",state="MI",panel="heavy_metals",title="Michigan heavy metal action limits",cite="Michigan CRA Sampling and Testing Technical Guidance v5.2 (Sept 23, 2024), Table 2",
      url="https://www.michigan.gov/cra/sections/enforcement-division/scientific-section",find=r'href="([^"]*Technical_Guidance_for_Marijuana_Products[^"]*\.pdf[^"]*)"',
      must=["Version 5.2","Lead 1.00 Inorganic Arsenic 0.400 Mercury 0.200 Cadmium 0.400 Total Chromium 1.200 Nickel* 1.000 Copper* N/A",
            "0.500 0.200 0.100 0.200 0.600 0.500 3.000+ 0.500 1.500 3.000 0.500 2.000 N/A N/A"],unit="µg/g",
      flower=dict(lead=1.0,arsenic=0.4,mercury=0.2,cadmium=0.4,chromium=1.2,nickel=1.0),
      concentrate=dict(lead=0.5,arsenic=0.2,mercury=0.1,cadmium=0.2,chromium=0.6,nickel=0.5,copper=3.0),
      other=dict(lead=0.5,arsenic=1.5,mercury=3.0,cadmium=0.5,chromium=2.0),
      text="Inhaled flower / inhaled concentrates / other products, ppm (µg/g). Arsenic is inorganic arsenic. Copper applies to vaping products only."),
 dict(id="mi_micro",state="MI",panel="microbials",title="Michigan microbial, mycotoxin and water activity limits",cite="Michigan CRA Sampling and Testing Technical Guidance v5.2, Tables 3 and 6",
      url="https://www.michigan.gov/cra/sections/enforcement-division/scientific-section",find=r'href="([^"]*Technical_Guidance_for_Marijuana_Products[^"]*\.pdf[^"]*)"',
      must=["Version 5.2","Medical Total Yeast & Mold 10,000 10,000 Count Adult-Use 100,000 10,000 Total Yeast & Mold Count Total Coliform 1000 100",
            "Aflatoxin B1 <20 Aflatoxin B2 <20 Aflatoxin G1 <20 Aflatoxin G2 <20 Ochratoxin A <20","does not exceed 0.65 aw","does not exceed 0.85 aw"],
      yeast_mold_cfu=dict(flower_adult_use=100000,flower_medical=10000,infused=10000),coliform_cfu=dict(flower=1000,infused=100),
      each_mycotoxin_ppb=20,water_activity=dict(flower=0.65,edible=0.85),
      text="Not detected in 1 g: STEC E. coli, Salmonella, Aspergillus flavus, fumigatus, niger and terreus. Total yeast and mold: 100,000 CFU/g (adult-use flower), 10,000 (medical flower and infused products). Total coliform: 1,000 CFU/g flower, 100 infused. Each aflatoxin (B1, B2, G1, G2) and ochratoxin A under 20 ppb. Water activity: 0.65 aw flower, 0.85 aw edibles."),
]
