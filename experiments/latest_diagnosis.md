# Failure summary for `iter11` (train)

Benchmark queries: 140; unanswerable: 30

Buckets at k=8: {"full": 87, "wrong_section": 11, "false_abstention": 11, "partial": 23, "near_miss": 8}
Relevant passage exists but ranked below 8: 18.6%
Relevant passage absent from all candidates: 1.4%
False answers on unanswerable queries by type: {"absent_clause": 7, "out_of_scope": 2}

## wrong_section
- `q003` Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; Are there any exceptions to competitive restrictions in this contract?
  - gold: BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT chars 33572-34034; first hit rank: 16; gap to gold in top 8: 4082
  - top passage: BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT chars 41051-41562 (score 0.1232)
- `q004` Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; Does this contract include any right of first refusal, right of first offer, or right of fi
  - gold: BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT chars 6235-6531; first hit rank: 35; gap to gold in top 8: 4436
  - top passage: BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT chars 52986-53399 (score -5.2783)
- `q035` Consider the Strategic Alliance Agreement between Information System Associates, Inc. and Rubicon Software Group plc; Does this contract include an exclusivity agreement?
  - gold: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT chars 5690-6079; first hit rank: 34; gap to gold in top 8: 24581
  - top passage: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT chars 37220-37778 (score -4.287)

## near_miss
- `q019` Consider the Service Agreement between Theravance Biopharma UK Limited and Brett Haumann; Is there a covenant not to sue included in this contract?
  - gold: THERAVANCEBIOPHARMA,INC 05 08 2020-EX-10.2-SERVICE AGREEMENT chars 27816-28397; first hit rank: 10; gap to gold in top 8: 1387
  - top passage: THERAVANCEBIOPHARMA,INC 05 08 2020-EX-10.2-SERVICE AGREEMENT chars 31498-32008 (score -5.7359)
- `q055` Consider the Intellectual Property Agreement for COVID-19 Treatment Development between Marv Enterprises, LLC, Premier Biomedical, Inc., and Technology Health, Inc.; Does this contract include an excl
  - gold: PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT chars 3388-4736; first hit rank: 13; gap to gold in top 8: 1125
  - top passage: PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT chars 21382-21737 (score -5.3498)
- `q082` Consider the Promotion Agreement between Depomed, Inc. and King Pharmaceuticals, Inc. for Glumetza; Does this contract include an exclusivity agreement?
  - gold: KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT chars 144427-144889; first hit rank: 38; gap to gold in top 8: 1296
  - top passage: KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT chars 153957-154328 (score -3.7784)

## partial
- `q010` Consider the Cooperation Agreement between HPIL ENERGYTECH Inc. and GINARES GROUP AG for Renewable Energy Projects; Is there a cap on liability under this contract?
  - gold: HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT chars 11380-11583; first hit rank: 6; gap to gold in top 8: 0
  - top passage: HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT chars 17853-18342 (score -2.463)
- `q024` Consider the Sponsorship Agreement between Excite, Inc. and Vitamin Shoppe Industries Inc. for Promotion on WebCrawler Channels; What is the expiration date of this contract?
  - gold: VITAMINSHOPPECOMINC 09 13 1999-EX-10.26-SPONSORSHIP AGREEMENT chars 33237-33842; first hit rank: 8; gap to gold in top 8: 0
  - top passage: VITAMINSHOPPECOMINC 09 13 1999-EX-10.26-SPONSORSHIP AGREEMENT chars 34203-34766 (score 0.453)
- `q039` Consider the Strategic Alliance Agreement between Information System Associates, Inc. and Rubicon Software Group plc; How is intellectual property ownership assigned in this contract?
  - gold: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT chars 14401-14603; first hit rank: 6; gap to gold in top 8: 0
  - top passage: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT chars 17753-18240 (score 2.0709)

## false_abstention
- `q009` Consider the Cooperation Agreement between HPIL ENERGYTECH Inc. and GINARES GROUP AG for Renewable Energy Projects; Is there an anti-assignment clause in this contract?
  - gold: HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT chars 17341-17432; first hit rank: 11; gap to gold in top 8: 421
  - top passage: HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT chars 18962-19355 (score -5.8884)
  - abstained: low_confidence
- `q050` Consider the Supply Agreement between Florida Chemical Company, LLC and Flotek Chemistry, LLC for Terpene Products; Does this contract include any volume restrictions?
  - gold: FLOTEKINDUSTRIESINCCN 05 09 2019-EX-10.1-SUPPLY AGREEMENT chars 958-1076; first hit rank: 26; gap to gold in top 8: 2562
  - top passage: FLOTEKINDUSTRIESINCCN 05 09 2019-EX-10.1-SUPPLY AGREEMENT chars 7658-8140 (score -7.1551)
  - abstained: low_confidence
- `q056` Consider the Intellectual Property Agreement for COVID-19 Treatment Development between Marv Enterprises, LLC, Premier Biomedical, Inc., and Technology Health, Inc.; Does this contract include any rev
  - gold: PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT chars 11296-11663; first hit rank: 19; gap to gold in top 8: 16
  - top passage: PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT chars 21382-21737 (score -7.1599)
  - abstained: low_confidence

## false_answer
- `u001` Consider the Support and Maintenance Agreement between On2 Technologies, Inc. and Wildform, Inc.; Is there a non-disparagement clause in this contract?
  - top passage: ON2TECHNOLOGIES,INC 11 17 2006-EX-10.3-SUPPORT AND MAINTENANCE AGREEMENT chars 14041-14556 (score -4.2844)
- `u002` Consider the Marketing Agreement between Loop Industries, Inc. and Indorama Loop Technologies, LLC for Product Supply and Development; What are the insurance requirements under this contract?
  - top passage: Loop Industries, Inc. - Marketing Agreement chars 18850-19365 (score -3.7302)
- `u004` Consider the Marketing and Transportation Services Agreement between Purolator Courier Ltd. and Parcelway Courier Systems Canada Ltd. (Dynamex Inc.); Are there any third-party beneficiaries designated
  - top passage: DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT chars 42698-43214 (score -2.65)
