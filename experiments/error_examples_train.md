# Failure examples from `20261102-010859_final_train`

## wrong_section (11 queries)

### `q003` (benchmark)
- Question: Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; Are there any exceptions to competitive restrictions in this contract?
- Gold (BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT, chars 33572-34034): save that nothing in this paragraph 13.2 shall prevent you from holding (with the prior written consent of the Company, which shall not be unreasonably delayed or withheld) up to three percent (3%) of the issued equity share capital of any company where those equity shares are listed on a recognised ...
- First relevant rank: 16; gap to gold in top k: 4082
- Routed to: BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT (coverage 1.0)
- Top passage (BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT, chars 41051-41562, score 0.1232): 14.4 For the avoidance of doubt nothing in this paragraph 14 shall prevent you from having any dealings with any Prospective Customer or Restricted Customer in relation to any business which is not Restricted Businesses and which is not competitive with the Restricted Business, nor from continuing t ...
- Diagnosis: TODO

### `q004` (benchmark)
- Question: Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; Does this contract include any right of first refusal, right of first offer, or right of first negotiation?
- Gold (BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT, chars 6235-6531): On or as soon as practicable following the Effective Date, it is intended that you will be granted an option under the Option Plan to acquire 107,417 ordinary shares in the capital of BTL ("Shares") (representing approximately 0.6% of the Company's issued share capital as at the Effective Date).
- First relevant rank: 35; gap to gold in top k: 4436
- Routed to: BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT (coverage 1.0)
- Top passage (BICYCLETHERAPEUTICSPLC 03 10 2020-EX-10.11-SERVICE AGREEMENT, chars 52986-53399, score -5.2783): 18.10 We reserve the right to amend the documents referred to above from time to time. 19 THIRD PARTY RIGHTS Save in respect of any rights conferred by this Agreement on any Group Company (which such Group Company shall be entitled to enforce), a person who is not a party to this Agreement may not u ...
- Diagnosis: TODO

### `q035` (benchmark)
- Question: Consider the Strategic Alliance Agreement between Information System Associates, Inc. and Rubicon Software Group plc; Does this contract include an exclusivity agreement?
- Gold (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 5690-6079): Rubicon hereby grants to ISA during the Term (as defined below) and subject to the exclusions described in 2.4 below an exclusive, non-transferable license in the United States to market, sell, use, display, perform, sublicense and distribute the Rubicon Offerings, the Documentation and, subject to  ...
- First relevant rank: 34; gap to gold in top k: 24581
- Routed to: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT (coverage 1.0)
- Top passage (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 37220-37778, score -4.287): This Agreement shall inure to the benefit of, and shall be binding upon, the Parties and their respective successors and permitted assigns. 11.3 Good Faith. The Parties undertake to act in good faith, consistent with their respective rights and obligations set forth in this Agreement. 11.4 Independe ...
- Diagnosis: TODO

## near_miss (8 queries)

### `q019` (benchmark)
- Question: Consider the Service Agreement between Theravance Biopharma UK Limited and Brett Haumann; Is there a covenant not to sue included in this contract?
- Gold (THERAVANCEBIOPHARMA,INC 05 08 2020-EX-10.2-SERVICE AGREEMENT, chars 27816-28397): If the Executive's employment is terminated at any time by reason of any reconstruction or amalgamation of any Group Company, whether by winding up or otherwise, and the Executive is offered employment with any concern or undertaking involved in or resulting from the reconstruction or amalgamation o ...
- First relevant rank: 10; gap to gold in top k: 1387
- Routed to: THERAVANCEBIOPHARMA,INC 05 08 2020-EX-10.2-SERVICE AGREEMENT (coverage 1.0)
- Top passage (THERAVANCEBIOPHARMA,INC 05 08 2020-EX-10.2-SERVICE AGREEMENT, chars 31498-32008, score -5.7359): 24.9 This Agreement may be executed in any number of counterparts, each of which, when executed and delivered, shall be an original, and all the counterparts together shall constitute one and the same agreement. 24.10 The Contracts (Rights of Third Parties) Act 1999 shall only apply to this Agreemen ...
- Diagnosis: TODO

### `q055` (benchmark)
- Question: Consider the Intellectual Property Agreement for COVID-19 Treatment Development between Marv Enterprises, LLC, Premier Biomedical, Inc., and Technology Health, Inc.; Does this contract include an exclusivity agreement?
- Gold (PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT, chars 3388-4736): The licenses granted herein are exclusive worldwide licenses to: 1. make, have made, use, lease, sell and import Licensed Products for the legal purposes of researching, developing, manufacturing, assembling, distributing, and selling the Licensed Products; 2. make, have made, use and import machine ...
- First relevant rank: 13; gap to gold in top k: 1125
- Routed to: PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT (coverage 1.0)
- Top passage (PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT, chars 21382-21737, score -5.3498): This Agreement, along with the exhibits hereto, sets forth the entire agreement and understanding of the Parties hereto and supersedes any and all prior arrangements and understandings related to the subject matter hereof except for as specifically stated in this Agreement with regards to the 2010 A ...
- Diagnosis: TODO

### `q082` (benchmark)
- Question: Consider the Promotion Agreement between Depomed, Inc. and King Pharmaceuticals, Inc. for Glumetza; Does this contract include an exclusivity agreement?
- Gold (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 144427-144889): Depomed agrees to grant and hereby grants to King an exclusive option (exercisable at King's sole discretion by providing written notice of intent at any time, but in no event later than 180 days after the Effective Date) to obtain an exclusive license in the Territory to certain of Depomed's propri ...
- First relevant rank: 38; gap to gold in top k: 1296
- Routed to: KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT (coverage 0.7439)
- Top passage (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 153957-154328, score -3.7784): Section 16.3 Entire Agreement. This Agreement, together with the schedules and exhibits hereto and the Confidentiality Agreement, all of which are incorporated by reference, contains all of the terms agreed to by the parties regarding the subject matter hereof and supersedes any prior agreements, un ...
- Diagnosis: TODO

## partial (23 queries)

### `q010` (benchmark)
- Question: Consider the Cooperation Agreement between HPIL ENERGYTECH Inc. and GINARES GROUP AG for Renewable Energy Projects; Is there a cap on liability under this contract?
- Gold (HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT, chars 11380-11583): GINARES agrees that the sole and exclusive remedy for money damages related to this Agreement and the transactions contemplated hereby shall be the rights to indemnification set forth in this Section 9.
- First relevant rank: 6; gap to gold in top k: 0
- Routed to: HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT (coverage 0.8002)
- Top passage (HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT, chars 17853-18342, score -2.463): 20. No Reliance No third party is entitled to rely on any of the representations, warranties and agreements contained in this Agreement. The Parties assume no liability to any third party because of any reliance on the representations, warranties and agreements contained in this Agreement. 21. Early ...
- Diagnosis: TODO

### `q024` (benchmark)
- Question: Consider the Sponsorship Agreement between Excite, Inc. and Vitamin Shoppe Industries Inc. for Promotion on WebCrawler Channels; What is the expiration date of this contract?
- Gold (VITAMINSHOPPECOMINC 09 13 1999-EX-10.26-SPONSORSHIP AGREEMENT, chars 33237-33842): Unless terminated earlier in accordance with the specific terms of this Agreement, the term of this Agreement will begin on the Launch Date and will not end until Excite displays a total of [*****] impressions of the Client advertising banners and promotional placements on the Excite Network as desc ...
- First relevant rank: 8; gap to gold in top k: 0
- Routed to: VITAMINSHOPPECOMINC 09 13 1999-EX-10.26-SPONSORSHIP AGREEMENT (coverage 1.0)
- Top passage (VITAMINSHOPPECOMINC 09 13 1999-EX-10.26-SPONSORSHIP AGREEMENT, chars 34203-34766, score 0.453): b) Either party may terminate this Agreement if the other party materially breaches its obligations hereunder and such breach remains uncured for thirty (30) days following the notice to the breaching party of the breach. c) All undisputed payments that have accrued prior to the termination or expir ...
- Diagnosis: TODO

### `q039` (benchmark)
- Question: Consider the Strategic Alliance Agreement between Information System Associates, Inc. and Rubicon Software Group plc; How is intellectual property ownership assigned in this contract?
- Gold (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 14401-14603): As regards Intellectual Property created by Rubicon, Rubicon acknowledges and agrees that those Works, as defined below, shall belong exclusively to ISA subject to payment in accordance with clause 4.2
- First relevant rank: 6; gap to gold in top k: 0
- Routed to: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT (coverage 1.0)
- Top passage (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 17753-18240, score 2.0709): ISA acknowledges that, except as otherwise set forth herein, neither it nor any other persons or entities will by virtue of this Agreement acquire any ownership interest in such Intellectual Property, or the Intellectual Property rights inherent in or appurtenant to any of the foregoing, or any asso ...
- Diagnosis: TODO

## false_abstention (11 queries)

### `q009` (benchmark)
- Question: Consider the Cooperation Agreement between HPIL ENERGYTECH Inc. and GINARES GROUP AG for Renewable Energy Projects; Is there an anti-assignment clause in this contract?
- Gold (HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT, chars 17341-17432): The rights and obligations provided by this Agreement shall not be assignable by any Party.
- First relevant rank: 11; gap to gold in top k: 421
- Routed to: HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT (coverage 0.8002)
- Top passage (HPILHOLDING 01 07 2015-EX-99.1-COOPERATION AGREEMENT, chars 18962-19355, score -5.8884): No amendment, supplement, modification, waiver or termination of this Agreement shall be implied or be binding (including, without limitation, any alleged waiver based on a Party's knowledge of any inaccuracy in any representation or warranty contained herein) unless in writing and signed by the Par ...
- Abstained: low_confidence (gate score -5.888422966003418)
- Diagnosis: TODO

### `q050` (benchmark)
- Question: Consider the Supply Agreement between Florida Chemical Company, LLC and Flotek Chemistry, LLC for Terpene Products; Does this contract include any volume restrictions?
- Gold (FLOTEKINDUSTRIESINCCN 05 09 2019-EX-10.1-SUPPLY AGREEMENT, chars 958-1076): "Maximum Quantity" means [***] pounds of Terpene Product per Year, prorated for any partial Year included in the Term.
- First relevant rank: 26; gap to gold in top k: 2562
- Routed to: FLOTEKINDUSTRIESINCCN 05 09 2019-EX-10.1-SUPPLY AGREEMENT (coverage 1.0)
- Top passage (FLOTEKINDUSTRIESINCCN 05 09 2019-EX-10.1-SUPPLY AGREEMENT, chars 7658-8140, score -7.1551): The recipient party shall hold in confidence any technical or business information the recipient party may learn, observe or otherwise obtain concerning the other party hereto, or of its Affiliates, incident to the recipient party's performance under the terms of this Agreement. These restrictions u ...
- Abstained: low_confidence (gate score -7.155125141143799)
- Diagnosis: TODO

### `q056` (benchmark)
- Question: Consider the Intellectual Property Agreement for COVID-19 Treatment Development between Marv Enterprises, LLC, Premier Biomedical, Inc., and Technology Health, Inc.; Does this contract include any revenue or profit-sharing arrangements?
- Gold (PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT, chars 11296-11663): Royalty payments are payable from THI to Marv Enterprises, LLC and will be in the amount of 5% of the Fair Market Value of: a. Licensed Product that is sold, leased or put into use by the THI or any Related Companies in the preceding calendar quarter; and b. any service performed by THI or any Relat ...
- First relevant rank: 19; gap to gold in top k: 16
- Routed to: PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT (coverage 1.0)
- Top passage (PREMIERBIOMEDICALINC 05 14 2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT, chars 21382-21737, score -7.1599): This Agreement, along with the exhibits hereto, sets forth the entire agreement and understanding of the Parties hereto and supersedes any and all prior arrangements and understandings related to the subject matter hereof except for as specifically stated in this Agreement with regards to the 2010 A ...
- Abstained: low_confidence (gate score -7.159862518310547)
- Diagnosis: TODO

## false_answer (9 queries)

### `u001` (absent_clause)
- Question: Consider the Support and Maintenance Agreement between On2 Technologies, Inc. and Wildform, Inc.; Is there a non-disparagement clause in this contract?
- Routed to: ON2TECHNOLOGIES,INC 11 17 2006-EX-10.3-SUPPORT AND MAINTENANCE AGREEMENT (coverage 1.0)
- Top passage (ON2TECHNOLOGIES,INC 11 17 2006-EX-10.3-SUPPORT AND MAINTENANCE AGREEMENT, chars 14041-14556, score -4.2844): 5.2 Exceptions to Non-Disclosure Obligations. Notwithstanding the foregoing, the Receiving Party shall be permitted to disclose Confidential Information without any violation of this Agreement if such disclosure is required by law, but in such event the Receiving Party shall notify the Disclosing Pa ...
- Diagnosis: TODO

### `u002` (absent_clause)
- Question: Consider the Marketing Agreement between Loop Industries, Inc. and Indorama Loop Technologies, LLC for Product Supply and Development; What are the insurance requirements under this contract?
- Routed to: Loop Industries, Inc. - Marketing Agreement (coverage 1.0)
- Top passage (Loop Industries, Inc. - Marketing Agreement, chars 18850-19365, score -3.7302): (iv) in public documents, in connection with the requirements of an initial public offering, secondary offering, or debt offering or any securities filing of the Parties; (v) in confidence, to accountants, banks, and financing sources and their advisors; (vi) in confidence, in connection with the en ...
- Diagnosis: TODO

### `u004` (absent_clause)
- Question: Consider the Marketing and Transportation Services Agreement between Purolator Courier Ltd. and Parcelway Courier Systems Canada Ltd. (Dynamex Inc.); Are there any third-party beneficiaries designated in this contract?
- Routed to: DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT (coverage 1.0)
- Top passage (DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT, chars 42698-43214, score -2.65): 34.0 CONFIDENTIAL INFORMATION 34.1 The Parties recognize that this Agreement contains information which is commercially sensitive and agree to keep the entire contents of this Agreement confidential and not to make any disclosures to any third Parties (other than their professional and financial adv ...
- Diagnosis: TODO

