# Failure examples from `20261102-011326_final_test`

## wrong_section (3 queries)

### `q045` (benchmark)
- Question: Consider the Strategic Alliance Agreement between Information System Associates, Inc. and Rubicon Software Group plc; Is there a covenant not to sue included in this contract?
- Gold (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 13844-13911): Rubicon shall not contest ownership by ISA of any of the foregoing.
- First relevant rank: 11; gap to gold in top k: 5655
- Routed to: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT (coverage 1.0)
- Top passage (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 29018-29410, score -5.3966): ISA hereby represents, covenants and warrants to Rubicon that: 9.1.1 It has the corporate power to enter into this Agreement; 9.1.2 It has the right to perform its obligations this Agreement; 9.1.3 When executed and delivered by it, this Agreement will constitute a legal, valid and binding obligatio ...
- Diagnosis: TODO

### `q081` (benchmark)
- Question: Consider the Promotion Agreement between Depomed, Inc. and King Pharmaceuticals, Inc. for Glumetza; Is there a non-compete clause in this contract?
- Gold (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 28888-29204): Except as expressly contemplated by this Agreement (including Article XIII hereof) and subject to Section 13.1 hereof, King shall not promote, market or distribute any product containing metformin hydrochloride as the sole active ingredient in the Territory during the Term of this Agreement, other t ...
- First relevant rank: None; gap to gold in top k: 24527
- Routed to: KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT (coverage 0.7439)
- Top passage (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 145298-145584, score 2.8656): and it is agreed that, as part of such good faith negotiations, the parties will discuss, for inclusion in any definitive agreement, appropriate non-compete obligations for each party with respect to any product containing metformin hydrochloride as an active pharmaceutical ingredient.
- Diagnosis: TODO

### `q093` (benchmark)
- Question: Consider the Promotion Agreement between Depomed, Inc. and King Pharmaceuticals, Inc. for Glumetza; Is there a covenant not to sue included in this contract?
- Gold (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 64934-65583): King recognizes Depomed's title to the Depomed Trademarks, and shall not at any time, during or after the Term, do or knowingly suffer to be done any act or thing which will in any way impair the rights of Depomed in or to the Depomed Trademarks. King acknowledges and agrees that it shall not acquir ...
- First relevant rank: 30; gap to gold in top k: 24979
- Routed to: KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT (coverage 0.7439)
- Top passage (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 132946-133290, score 4.5664): in recognition of the parties' agreement to co-exclusively Promote Products, in accordance with the terms and conditions of this Agreement, Depomed agrees that if Depomed or any Affiliate thereof grants to any Affiliate or Third Party a license, covenant not to sue, right of reference, right of supp ...
- Diagnosis: TODO

## near_miss (6 queries)

### `q023` (benchmark)
- Question: Consider the Sponsorship Agreement between R. C. Boyd Enterprises, LLC and Cano Petroleum, Inc. for 'Honey Hole'; Is there a minimum commitment required under this contract?
- Gold (CANOPETROLEUM,INC 12 13 2007-EX-10.1-Sponsorship Agreement, chars 1116-1204): The Company shall produce no less than forty (40) original episodes of the Show per year
- First relevant rank: 9; gap to gold in top k: 1223
- Routed to: CANOPETROLEUM,INC 12 13 2007-EX-10.1-Sponsorship Agreement (coverage 1.0)
- Top passage (CANOPETROLEUM,INC 12 13 2007-EX-10.1-Sponsorship Agreement, chars 7687-7821, score -5.5328): not set forth in this contract, and that no agreement, statement, or promise not contained in this contract shall be valid or binding.
- Diagnosis: TODO

### `q042` (benchmark)
- Question: Consider the Strategic Alliance Agreement between Information System Associates, Inc. and Rubicon Software Group plc; Are there any services to be provided after the termination of this contract?
- Gold (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 12612-12792): Each Party shall retain the financial records relating to all payments owed and/or paid under this Agreement for a period of six years from the date such payment obligation arose.
- First relevant rank: 61; gap to gold in top k: 710
- Routed to: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT (coverage 1.0)
- Top passage (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 20121-20715, score -0.2895): Either Party may terminate this Agreement upon ten Business Day's Notice to the other Party in the event the other Party contests or challenges to a material degree any of the other Party's Intellectual Property rights referred to in Sections 5.1, and 5.3, respectively. 7. NON-COMPETITION. 7.1 Durin ...
- Diagnosis: TODO

### `q063` (benchmark)
- Question: Consider the Marketing and Transportation Services Agreement between Purolator Courier Ltd. and Parcelway Courier Systems Canada Ltd. (Dynamex Inc.); Does this contract include an exclusivity agreement?
- Gold (DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT, chars 7970-8101): Dynamex agrees not to provide sameday delivery services for any other provider of next day or multiple day courier services.
- First relevant rank: None; gap to gold in top k: 1197
- Routed to: DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT (coverage 1.0)
- Top passage (DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT, chars 9298-9504, score -5.2751): It is understood and agreed that nothing in this Agreement shall prevent the Parties from continuing to provide such services or their continued development of such services/operations.
- Diagnosis: TODO

### `q114` (benchmark)
- Question: Consider the Endorsement Agreement between ABG-Shaq, LLC and Papa John's International, Inc.; What licenses are granted under this contract?
- Gold (Papa Johns International Inc 20190617 8-K EX-10.1 11707365 EX-10.1 Endorsement Agreement, chars 3851-4268): In consideration of the remuneration to be paid to ABG pursuant hereto and subject to the conditions and limitations contained herein, ABG grants to PAPA JOHN'S the non-transferrable, non-assignable, non-sublicensable, indivisible right and license solely during the Term of the Agreement and within  ...
- First relevant rank: None; gap to gold in top k: 173
- Routed to: Papa Johns International Inc 20190617 8-K EX-10.1 11707365 EX-10.1 Endorsement Agreement (coverage 1.0)
- Top passage (Papa Johns International Inc 20190617 8-K EX-10.1 11707365 EX-10.1 Endorsement Agreement, chars 17036-17591, score -1.7023): 4. Services. To facilitate PAPA JOHN'S usage of the right and license to the Celebrity Endorsement with respect to the Products as provided herein, during each Contract Year during the Term of the Agreement, subject to CELEBRITY's prior personal and professional obligations, and further subject to a ...
- Diagnosis: TODO

## partial (10 queries)

### `q043` (benchmark)
- Question: Consider the Strategic Alliance Agreement between Information System Associates, Inc. and Rubicon Software Group plc; Is there uncapped liability under this contract?
- Gold (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 32028-32397): EXCEPT IN CONNECTION WITH A BREACH BY EITHER PARTY OF SECTION 8, NEITHER PARTY WILL BE LIABLE FOR ANY SPECIAL, INDIRECT, CONSEQUENTIAL, EXEMPLARY, PUNITIVE OR INCIDENTAL DAMAGES ARISING OUT OF OR RELATED TO THIS AGREEMENT, HOWEVER CAUSED AND UNDER ANY THEORY OF LIABILITY (INCLUDING NEGLIGENCE), EVEN ...
- First relevant rank: 1; gap to gold in top k: 0
- Routed to: DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT (coverage 1.0)
- Top passage (DUOSTECHNOLOGIESGROUP,INC 04 21 2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT, chars 32028-32503, score -3.9097): EXCEPT IN CONNECTION WITH A BREACH BY EITHER PARTY OF SECTION 8, NEITHER PARTY WILL BE LIABLE FOR ANY SPECIAL, INDIRECT, CONSEQUENTIAL, EXEMPLARY, PUNITIVE OR INCIDENTAL DAMAGES ARISING OUT OF OR RELATED TO THIS AGREEMENT, HOWEVER CAUSED AND UNDER ANY THEORY OF LIABILITY (INCLUDING NEGLIGENCE), EVEN ...
- Diagnosis: TODO

### `q071` (benchmark)
- Question: Consider the Marketing and Transportation Services Agreement between Purolator Courier Ltd. and Parcelway Courier Systems Canada Ltd. (Dynamex Inc.); What are the insurance requirements under this contract?
- Gold (DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT, chars 19106-20201): Each Party shall purchase and maintain, at its own expense, the following insurance coverages: (a) cargo liability insurance, subject to a combined single limit of not less than One Hundred Thousand dollars ($100,000.00) inclusive per occurrence. The other Party shall be named as an additional insur ...
- First relevant rank: 2; gap to gold in top k: 0
- Routed to: DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT (coverage 1.0)
- Top passage (DYNAMEXINC 06 06 1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT, chars 21316-21847, score 1.0287): 9.5 The policies set out in paragraph 9.1 shall not limit the insurance required by municipal, provincial, federal or other law. It shall be the sole responsibility of each Party to determine what additional insurance coverages, if any, are necessary and advisable for its own protection 9 - 9 - or t ...
- Diagnosis: TODO

### `q083` (benchmark)
- Question: Consider the Promotion Agreement between Depomed, Inc. and King Pharmaceuticals, Inc. for Glumetza; Does this contract include any right of first refusal, right of first offer, or right of first negotiation?
- Gold (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 144427-146183): Depomed agrees to grant and hereby grants to King an exclusive option (exercisable at King's sole discretion by providing written notice of intent at any time, but in no event later than 180 days after the Effective Date) to obtain an exclusive license in the Territory to certain of Depomed's propri ...
- First relevant rank: 1; gap to gold in top k: 0
- Routed to: KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT (coverage 0.7439)
- Top passage (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 147301-147892, score -0.1581): Patent Nos. 6,340,475 and 6,635,280. Section 13.2 Right of First Negotiation. Depomed shall notify King in writing in the event that Depomed desires to divest itself of its rights to the Product in the Territory (e.g., by asset sale or product license to a Third Party), or of its rights in the Terri ...
- Diagnosis: TODO

### `q086` (benchmark)
- Question: Consider the Promotion Agreement between Depomed, Inc. and King Pharmaceuticals, Inc. for Glumetza; Is there a minimum commitment required under this contract?
- Gold (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 42251-42711): From and after the Promotion Commencement Date, King shall perform at least [***] PDEs per calendar year, with such amount prorated over the initial and final calendar years of the Term if either such year is a partial year. In fulfilling its obligations under this Section 4.1(b), King will perform  ...
- First relevant rank: 3; gap to gold in top k: 0
- Routed to: KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT (coverage 0.7439)
- Top passage (KINGPHARMACEUTICALSINC 08 09 2006-EX-10.1-PROMOTION AGREEMENT, chars 119034-119270, score -2.0646): In addition, any other provisions required to interpret and enforce the parties' rights and obligations under this Agreement shall also survive, but only to the extent required for the full observation and performance of this Agreement.
- Diagnosis: TODO

## false_abstention (2 queries)

### `q112` (benchmark)
- Question: Consider the Endorsement Agreement between ABG-Shaq, LLC and Papa John's International, Inc.; Does this contract include any volume restrictions?
- Gold (Papa Johns International Inc 20190617 8-K EX-10.1 11707365 EX-10.1 Endorsement Agreement, chars 17729-17939): At least eight (8) "Service Days", including but not limited to: 1. Production days. Up to four (4) production days (defined as a maximum of eight (8) consecutive hours each), with PAPA JOHN'S creative agency.
- First relevant rank: 52; gap to gold in top k: 4380
- Routed to: Papa Johns International Inc 20190617 8-K EX-10.1 11707365 EX-10.1 Endorsement Agreement (coverage 1.0)
- Top passage (Papa Johns International Inc 20190617 8-K EX-10.1 11707365 EX-10.1 Endorsement Agreement, chars 13327-13349, score -6.8928): 5. Brand Restrictions.
- Abstained: low_confidence (gate score -6.892755508422852)
- Diagnosis: TODO

### `q134` (benchmark)
- Question: Consider the Business Affiliate Agreement between Dr. George D. Green and UNION DENTAL CORP.; What are the audit rights under this contract?
- Gold (Union Dental Holdings Inc 20050204 8-KA EX-10 3345577 EX-10 Affiliate Agreement, chars 3636-4076): Make available, during normal business hours, at a Party=s offices all records, books, agreements, policies and procedures relating to the use and/or disclosure of Confidential Information that is subject to this Agreement, to the other Party within ten (10) days of a Party's written request, for th ...
- First relevant rank: 15; gap to gold in top k: 15
- Routed to: Union Dental Holdings Inc 20050204 8-KA EX-10 3345577 EX-10 Affiliate Agreement (coverage 1.0)
- Top passage (Union Dental Holdings Inc 20050204 8-KA EX-10 3345577 EX-10 Affiliate Agreement, chars 8402-8885, score -6.0601): 7. Miscellaneous. a. Survival. The respective rights and obligations of Business Affiliate and UDC under the provisions of Sections 3(g) [Responsibilities of the Parties] and 3(h) [Responsibilities of the Parties] and 6 shall survive the termination of this Agreement indefinitely. 3 b. Amendment. Th ...
- Abstained: low_confidence (gate score -6.060084819793701)
- Diagnosis: TODO

## false_answer (3 queries)

### `u011` (absent_clause)
- Question: Consider the Sponsorship Agreement between Excite, Inc. and Vitamin Shoppe Industries Inc. for Promotion on WebCrawler Channels; Are there any price restrictions or controls specified in this contract?
- Routed to: VITAMINSHOPPECOMINC 09 13 1999-EX-10.26-SPONSORSHIP AGREEMENT (coverage 1.0)
- Top passage (VITAMINSHOPPECOMINC 09 13 1999-EX-10.26-SPONSORSHIP AGREEMENT, chars 53106-53545, score -4.0945): c) EXCEPT AS SPECIFIED IN THIS AGREEMENT, NEITHER PARTY MAKES ANY WARRANTY IN CONNECTION WITH THE SUBJECT MATTER OF THIS AGREEMENT AND HEREBY DISCLAIMS ANY AND ALL IMPLIED WARRANTIES, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE REGARDING SUCH SUBJECT MATT ...
- Diagnosis: TODO

### `u018` (absent_clause)
- Question: Consider the Endorsement Agreement between Holiday RV Superstores, Inc. and Affinity Group, Inc. for Good Sam Branding; What happens in the event of a change of control of one of the parties in this contract?
- Routed to: HOLIDAYRVSUPERSTORESINC 04 15 2002-EX-10.13-ENDORSEMENT AGREEMENT (coverage 0.9229)
- Top passage (HOLIDAYRVSUPERSTORESINC 04 15 2002-EX-10.13-ENDORSEMENT AGREEMENT, chars 5108-5680, score -3.6124): Date"). In the event that the Company desires to terminate the Agreement prior to the Termination Date, it shall provide AGI with at least 60 days prior written notice of its intention to terminate this Agreement and this Agreement shall so terminate following the expiration of this 60-day period, w ...
- Diagnosis: TODO

### `u045` (out_of_scope)
- Question: Consider the Sponsorship Agreement between Jacksonville Jaguars, LLC and The ARC Group, Inc.; Who founded each of the parties to this contract?
- Routed to: Arc Group Inc 20171211 8-K EX-10.1 10976103 EX-10.1 Sponsorship Agreement (coverage 1.0)
- Top passage (Arc Group Inc 20171211 8-K EX-10.1 10976103 EX-10.1 Sponsorship Agreement, chars 9118-9548, score -3.2041): IN WITNESS WHEREOF, each party has caused this Agreement to be executed in Jacksonville, Florida, by its duly authorized representative with the intent that it be binding as of the Execution Date. CLUB: SPONSOR: JACKSONVILLE JAGUARS, LLC The ARC Group, Inc. By: /s/ Scott Massey By: /s/ Richard W. Ak ...
- Diagnosis: TODO

