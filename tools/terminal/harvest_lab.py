"""Harvest PubMed for terpene lab, holistic pairings, drug interactions, cultivation. -> cache/lab.json"""
import json,sys,time
from harvest_pubmed import esearch,efetch
Q={
# compounds
"myrcene":["myrcene AND (sedative OR sedation OR analgesic OR anti-inflammatory)","myrcene AND (hops OR Humulus OR lemongrass OR mango)"],
"linalool":["linalool AND (anxiety OR anxiolytic) AND (inhalation OR mice OR humans)","linalool AND lavender AND (randomized controlled trial[pt] OR systematic review[pt])"],
"beta_caryophyllene":["beta-caryophyllene AND dietary cannabinoid AND CB2","beta-caryophyllene AND (pain OR inflammation) AND review[pt]"],
"limonene":["limonene AND (THC OR tetrahydrocannabinol) AND anxiety AND humans","limonene AND (anxiolytic OR stress) AND (citrus OR essential oil)"],
"alpha_pinene":["alpha-pinene AND (memory OR anti-inflammatory OR bronchodilator)","pinene AND cannabis AND review[pt]"],
"cbg":["cannabigerol AND (humans OR randomized controlled trial[pt] OR survey)","cannabigerol AND review[pt] AND pharmacology"],
"cbn":["cannabinol AND sleep AND (randomized controlled trial[pt] OR humans)","cannabinol AND (degradation OR oxidation) AND THC AND storage"],
"thcv":["tetrahydrocannabivarin AND (appetite OR glycemic OR diabetes OR humans)"],
"entourage":["(Taming THC OR entourage effect) AND terpenoids AND phytocannabinoid","cannabis terpenes AND review[pt] AND pharmacology AND (entourage OR synergy)"],
# holistic
"sleep_hygiene":["cognitive behavioral therapy for insomnia AND (meta-analysis[pt] OR guideline[pt])"],
"chronic_pain_lifestyle":["exercise therapy AND chronic pain AND (Cochrane OR systematic review[pt] OR meta-analysis[pt]) AND adults","mindfulness-based AND chronic pain AND meta-analysis[pt]"],
"fibro_lifestyle":["EULAR revised recommendations fibromyalgia management","exercise AND fibromyalgia AND Cochrane"],
"anxiety_lifestyle":["mindfulness-based stress reduction AND anxiety AND randomized controlled trial[pt] AND escitalopram","exercise AND anxiety AND meta-analysis[pt] AND adults"],
"ptsd_lifestyle":["(yoga OR mindfulness OR exercise) AND PTSD AND meta-analysis[pt]"],
"ibd_lifestyle":["(diet OR Mediterranean diet) AND (Crohn disease OR inflammatory bowel disease) AND (randomized controlled trial[pt] OR guideline[pt]) AND IOIBD OR ECCO"],
"migraine_lifestyle":["migraine AND (lifestyle OR aerobic exercise OR sleep OR trigger) AND (systematic review[pt] OR meta-analysis[pt])","cannabis AND medication overuse headache"],
"arthritis_lifestyle":["osteoarthritis AND (exercise OR weight loss) AND (guideline[pt] OR meta-analysis[pt]) AND knee","rheumatoid arthritis AND (Mediterranean diet OR exercise) AND systematic review[pt]"],
"ms_lifestyle":["multiple sclerosis AND exercise AND spasticity AND (systematic review[pt] OR meta-analysis[pt])"],
"cinv_lifestyle":["ginger AND chemotherapy-induced nausea AND (meta-analysis[pt] OR randomized controlled trial[pt])"],
"appetite_lifestyle":["cancer cachexia AND (nutrition OR exercise) AND (guideline[pt] OR ESPEN OR ASCO)"],
"epilepsy_lifestyle":["sleep deprivation AND seizures AND epilepsy AND triggers","ketogenic diet AND epilepsy AND Cochrane"],
"interactions":["cannabidiol AND warfarin AND (INR OR interaction)","cannabidiol AND drug interactions AND (CYP3A4 OR CYP2C19 OR CYP2C9) AND review[pt]","cannabidiol AND clobazam AND interaction","cannabis AND older adults AND (falls OR dizziness OR adverse events) AND meta-analysis[pt]","cannabis AND hyperemesis syndrome AND review[pt]","cannabis AND cardiovascular AND (myocardial infarction OR stroke) AND cohort"],
# cultivation
"cult_uvb":["Cannabis sativa AND (UV-B OR ultraviolet) AND cannabinoid","Cannabis AND ultraviolet AND terpene"],
"cult_light":["Cannabis sativa AND light spectrum AND (cannabinoid OR terpene) AND LED","Cannabis sativa AND light intensity AND yield AND cannabinoid"],
"cult_harvest":["Cannabis sativa AND harvest time AND (cannabinoid OR terpene OR trichome)","Cannabis AND trichome AND maturity AND cannabinoid"],
"cult_drying":["Cannabis AND (drying OR curing) AND (terpene OR volatile OR monoterpene)","Cannabis AND storage AND (temperature OR light) AND THC degradation AND CBN"],
"cult_stress":["Cannabis sativa AND (drought OR water stress) AND cannabinoid","Cannabis sativa AND (nutrient OR nitrogen OR phosphorus) AND cannabinoid AND inflorescence","Cannabis AND (defoliation OR pruning OR wounding OR methyl jasmonate) AND cannabinoid"],
"cult_genetics":["Cannabis AND chemotype AND (THCA synthase OR CBDA synthase) AND inheritance","Cannabis AND terpene AND (chemovar OR cultivar) AND classification AND (indica OR sativa) labels","Cannabis AND strain names AND (inconsistent OR chemical) AND (THC OR terpene)"],
"cult_cbg":["Cannabis AND cannabigerol AND (chemotype IV OR high-CBG OR CBGA) AND cultivar"],
"cult_thcv":["Cannabis AND (THCV OR tetrahydrocannabivarin OR propyl cannabinoids) AND (cultivar OR breeding OR genetics)"],
}
if __name__=="__main__":
    res={}
    for k,qs in Q.items():
        ids=[]
        for q in qs:
            try:
                for i in esearch(q,5):
                    if i not in ids: ids.append(i)
            except Exception as e: print("ERR",k,e,file=sys.stderr)
        res[k]={"queries":qs,"records":efetch(ids)}; print(k,len(res[k]["records"]),file=sys.stderr)
    res["_meta"]={"source":"NCBI PubMed E-utilities","fetched":time.strftime("%Y-%m-%d %H:%M %Z")}
    json.dump(res,open("cache/lab.json","w"),indent=1)
