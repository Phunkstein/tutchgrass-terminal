import json,sys
from harvest_pubmed import esearch,efetch
X={
"ptsd":["Bonn-Miller AND cannabis AND PTSD AND randomized","nabilone AND nightmares AND PTSD","cannabidiol AND PTSD"],
"ibd_crohns":["Naftali AND cannabis AND Crohn","cannabis AND Crohn AND THC AND CBD AND randomized controlled trial[pt]","beta-caryophyllene AND colitis"],
"insomnia":["cannabinol AND sleep","myrcene AND sedative","Walsh AND cannabis AND insomnia AND (THC OR CBN)"],
"appetite_cachexia":["dronabinol AND (HIV OR AIDS) AND appetite AND weight","Brisbois AND THC AND taste AND appetite","cannabigerol AND appetite AND hyperphagia","tetrahydrocannabivarin AND appetite"],
"anxiety":["linalool AND anxiolytic","cannabidiol AND public speaking AND anxiety"],
"arthritis":["Blake AND Sativex AND rheumatoid arthritis","cannabidiol AND arthritis AND (inflammation OR pain) AND rat"],
"migraine":["cannabis AND migraine AND survey AND (THC OR CBD) AND headache frequency"],
"fibromyalgia":["Habib AND cannabis AND fibromyalgia","nabilone AND fibromyalgia AND randomized"],
"chronic_neuropathic_pain":["Abrams AND vaporized AND sickle OR cannabis AND THC:CBD AND chronic pain AND ratio"],
}
d=json.load(open('cache/pubmed.json'))
for k,qs in X.items():
    have={r['pmid'] for r in d[k]['records']}
    ids=[]
    for q in qs:
        for i in esearch(q,5):
            if i not in have and i not in ids: ids.append(i)
    d[k]['records']+=efetch(ids); d[k]['queries']+=qs
    print(k,len(ids),file=sys.stderr)
json.dump(d,open('cache/pubmed.json','w'),indent=1)
