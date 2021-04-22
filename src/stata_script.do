
capture log close 
set logtype text
set more off 
log using "..\log_files\Misinformation-v14", replace



************* STATE LEVEL ANALYSES **************


clear

import excel "..\output_files\state_level_master_data--2021-04-16__22-51-06.xlsx", sheet("state_level_master_data--2021-0") firstrow
rename value v


gen var = subinstr(variable," ","",.)

gen var2 = subinstr(var,"100_accounts","a100",.)
gen var3 = subinstr(var2,"50_accounts","a50",.)
gen var4 = subinstr(var3,"10_accounts","a10",.)
gen var5 = subinstr(var4,"1_accounts","a1",.)

gen var6 = subinstr(var5,"100_tweets","t100",.)
gen var7 = subinstr(var6,"50_tweets","t50",.)
gen var8 = subinstr(var7,"10_tweets","t10",.)
gen var9 = subinstr(var8,"1_tweets","t1",.)

gen var10 = subinstr(var9,".","",.)
gen var11 = subinstr(var10,"%","Pct",.)
gen var12 = subinstr(var11,"low-credibility","LC",.)

gen var13 = subinstr(var12,"accounts","Accounts",.)
gen var14 = subinstr(var13,"tweets","Tweets",.)
gen var15 = subinstr(var14,"NonHispanic","NonHisp",.)
gen var16 = subinstr(var15,"NativeAmerican","NatAm",.)
gen var17 = subinstr(var16, "mean_smoothed_covid_vaccinated_or_accept","AcceptVaccineMean",.)
gen var18 = subinstr(var17, "stderr_smoothed_covid_vaccinated_or_accept","AcceptVaccineStderr",.)
gen var19 = subinstr(var18, "Percentofadultswithabachelor'sdegreeorhigher,2015-19","PercBachelors",.)
gen var20 = subinstr(var19, "sample_size_for_covid_vaccinated_or_accept_question", "CovidSampleSize",.)
gen var21 = subinstr(var20, "num_smoothed_covid_vaccinated_or_accept", "CovidNum",.)
gen var22 = subinstr(var21, "early_daily_vaccinations_per_million", "eardailyvaxpermill",.)
gen var23 = subinstr(var22, "early_people_fully_vaccinated_per_hundred", "earfullyvaxperhund",.)
gen var24 = subinstr(var23, "early_people_vaccinated_per_hundred", "earvaxperhund",.)
gen var25 = subinstr(var24, "people_fully_vaccinated_per_hundred", "fullyvaxperhund",.)


drop variable var-var24

rename var25 varshort

duplicates tag FIPS varshort, gen(dup)

fre dup

drop dup


reshape wide v, i(FIPS) j(varshort) string

sum FIPS

drop if vAcceptVaccineMean==.


sum FIPS





*Add weights to account for DV standard errors

gen paccept=vAcceptVaccineMean*100
lab var paccept "% acceptance of vaccine"
gen pstderr=vAcceptVaccineStderr*100

gen phesitancy=100-paccept
lab var phesitancy "% hesitant to get vaccine"

gen awgt=vCovidSampleSize
lab var awgt "Analytic weight for regressions"

*Rename misinformation variables to match county analysis

gen lowcred=vMeanPctLC
lab var lowcred "Mean % low credibility tweets"

drop if lowcred==.


gen gop=vprop_gop_vote
recode gop (0/.50=0)(.5000001/1=1)
lab var gop "Majority GOP state"


gen propgop=10*vprop_gop_vote
lab var propgop "% GOP vote (10% change)"

gen ppoverty=(vPOVALL_2019/vTotalPop2010)*100
lab var ppoverty "% below poverty line"

gen population=vTotalPop2010/100000
lab var population "Population in 100,000's"


*Decide which covid rate variable to use
pwcorr phesitancy vrecent_cases_cum vrecent_deaths_cum vtotal_cases_cum vtotal_deaths_cum, sig
*Total deaths 

gen covidmortality=(vtotal_deaths_cum/vTotalPop2010)*1000
lab var covidmortality "COVID deaths/thousand" 


gen vaxrate=vdaily_vaccinations_per_million
lab var vaxrate "Daily vaccinations/million"


lab var vAge65AndOlderPct2010 "% aged 65+"
lab var vAsianNonHispPct2010 "% Asian"
lab var vBlackNonHispPct2010 "% Black"
lab var vHispanicPct2010 "% Hispanic"
lab var vNatAmNonHispPct2010 "% Indigenous"



*low credit variables skewed - must use nonlinear transformation or polynomial
histogram paccept
histogram phesitancy
histogram lowcred
histogram vaxrate

gen loglowcred=log(.1+lowcred)
lab var loglowcred "Logged low credibility tweets"

histogram loglowcred
*slightly skewed at state level (check hettest)

*Descriptive statistics
sum phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop lowcred




*Bivariate correlations between candidated covariates
pwcorr phesitancy vaxrate lowcred loglowcred propgop covidmortality population vMedHHInc ppoverty vPercBachelors vUnemployment_rate_2019 vTOTRATE vUnder18Pct2010 vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010, sig  
*best SES variable is % with bachelors, but strongly correlated with gopvote



*test for multicollinearity
reg phesitancy lowcred propgop covidmortality ppoverty vPercBachelors vUnder18Pct2010 vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010
estat vif
*gopvote, age, poverty, and bachelors are collinear

*Which to keep?
reg phesitancy lowcred propgop covidmortality ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010
estat vif
*drop under18 and bachelors 
*this looks okay

reg vaxrate lowcred propgop covidmortality ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010
estat vif
*same as phesitancy


*test for heteroskedasticity
reg phesitancy lowcred propgop [aweight=awgt]
hettest
*homoskedastic

reg vaxrate lowcred propgop 
hettest
*homoskedastic


*multivariate analyses

*Vaccine acceptance

*Empty model
reg phesitancy [aweight=awgt]


* Restricted models - low cred and gop vote 

reg phesitancy lowcred propgop [aweight=awgt]
estat ic
estimates store a1, title(Model a1)


* Full models - low cred and gop vote, plus all controls 

reg phesitancy lowcred propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality [aweight=awgt]
estat ic
estimates store a2, title(Model a2)

*Vaccination rate

*Empty model
reg vaxrate

* Restricted models - low cred and gop vote 

reg vaxrate lowcred propgop
estat ic
estimates store a3, title(Model a3)

* Full models - low cred and gop vote, plus all controls 

reg vaxrate lowcred propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality
estat ic
hettest
estimates store a4, title(Model a4)


esttab a* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table1.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace




*FIGURES

*scatterplot
graph twoway (scatter phesitancy lowcred if gop==0) (scatter phesitancy lowcred if gop==1), ///
  legend(label(1 Dem) label(2 Rep)) 

graph twoway (scatter vaxrate lowcred if gop==0) (scatter vaxrate lowcred if gop==1), ///
  legend(label(1 Dem) label(2 Rep))   
  

reg phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop lowcred [aweight=awgt]
margins, at(lowcred=(0 .1 .2 .3 .4 .5 .6 .7 .8 .9 1))
marginsplot, ytitle(Predicted value) title("")

reg vaxrate ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop lowcred 
margins, at(lowcred=(0 .1 .2 .3 .4 .5 .6 .7 .8 .9 1))
marginsplot, ytitle(Predicted value) title("")


*Sensitivity analyses

*rerun with logged values of low credibility tweets
*results very similar, bic better for original variable and no heteroskedasticity

*Vaccine acceptance

*Empty model
reg phesitancy [aweight=awgt]


* Restricted models - low cred and gop vote (log)

reg phesitancy loglowcred propgop [aweight=awgt]
estat ic
estimates store b1, title(Model b1)

* Full models - low cred and gop vote, plus all controls (log)

reg phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop loglowcred [aweight=awgt]
estat ic
estimates store b2, title(Model b2)


*Empty model
reg vaxrate


* Restricted models - low cred and gop vote (log)

reg vaxrate loglowcred propgop
estat ic
estimates store b3, title(Model b3)


* Full models - low cred and gop vote, plus all controls (log)

reg vaxrate ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop loglowcred
estat ic
estimates store b4, title(Model b4)



esttab b* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table2.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace




*Sensitivity analyses - interactions

reg phesitancy lowcred gop [aweight=awgt]
estat ic

reg phesitancy c.lowcred##i.gop [aweight=awgt]
estat ic
*No interaction at state level

reg vaxrate lowcred gop 
estat ic

reg vaxrate c.lowcred##i.gop 
estat ic
*No interaction at state level




*Output clean file

keep FIPS paccept phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 ///
vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop loglowcred lowcred vaxrate gop awgt


export excel using "STATE_misinformation_clean-042221", replace firstrow(variables)







************* STATE LEVEL ANALYSES FILTERED **************

*Sensitivity analyses with filtered key words

clear

import excel "..\output_files\state_level_keywords_filtered_master_data--2021-04-16__22-51-11.xlsx", sheet("state_level_keywords_filtered_m") firstrow clear

rename value v


gen var = subinstr(variable," ","",.)

gen var2 = subinstr(var,"100_accounts","a100",.)
gen var3 = subinstr(var2,"50_accounts","a50",.)
gen var4 = subinstr(var3,"10_accounts","a10",.)
gen var5 = subinstr(var4,"1_accounts","a1",.)

gen var6 = subinstr(var5,"100_tweets","t100",.)
gen var7 = subinstr(var6,"50_tweets","t50",.)
gen var8 = subinstr(var7,"10_tweets","t10",.)
gen var9 = subinstr(var8,"1_tweets","t1",.)

gen var10 = subinstr(var9,".","",.)
gen var11 = subinstr(var10,"%","Pct",.)
gen var12 = subinstr(var11,"low-credibility","LC",.)

gen var13 = subinstr(var12,"accounts","Accounts",.)
gen var14 = subinstr(var13,"tweets","Tweets",.)
gen var15 = subinstr(var14,"NonHispanic","NonHisp",.)
gen var16 = subinstr(var15,"NativeAmerican","NatAm",.)
gen var17 = subinstr(var16, "mean_smoothed_covid_vaccinated_or_accept","AcceptVaccineMean",.)
gen var18 = subinstr(var17, "stderr_smoothed_covid_vaccinated_or_accept","AcceptVaccineStderr",.)
gen var19 = subinstr(var18, "Percentofadultswithabachelor'sdegreeorhigher,2015-19","PercBachelors",.)
gen var20 = subinstr(var19, "sample_size_for_covid_vaccinated_or_accept_question", "CovidSampleSize",.)
gen var21 = subinstr(var20, "num_smoothed_covid_vaccinated_or_accept", "CovidNum",.)
gen var22 = subinstr(var21, "early_daily_vaccinations_per_million", "eardailyvaxpermill",.)
gen var23 = subinstr(var22, "early_people_fully_vaccinated_per_hundred", "earfullyvaxperhund",.)
gen var24 = subinstr(var23, "early_people_vaccinated_per_hundred", "earvaxperhund",.)
gen var25 = subinstr(var24, "people_fully_vaccinated_per_hundred", "fullyvaxperhund",.)


drop variable var-var24

rename var25 varshort

duplicates tag FIPS varshort, gen(dup)

fre dup

drop dup


reshape wide v, i(FIPS) j(varshort) string

sum FIPS

drop if vAcceptVaccineMean==.


sum FIPS





*Add weights to account for DV standard errors

gen paccept=vAcceptVaccineMean*100
lab var paccept "% acceptance of vaccine"
gen pstderr=vAcceptVaccineStderr*100

gen phesitancy=100-paccept
lab var phesitancy "% hesitant to get vaccine"

gen awgt=vCovidSampleSize
lab var awgt "Analytic weight for regressions"

*Rename misinformation variables to match county analysis

gen lowcred=vMeanPctLC
lab var lowcred "Mean % low credibility tweets"

drop if lowcred==.


gen gop=vprop_gop_vote
recode gop (0/.50=0)(.5000001/1=1)
lab var gop "Majority GOP state"


gen propgop=10*vprop_gop_vote
lab var propgop "% GOP vote (10% change)"

gen ppoverty=(vPOVALL_2019/vTotalPop2010)*100
lab var ppoverty "% below poverty line"

gen population=vTotalPop2010/100000
lab var population "Population in 100,000's"

gen covidmortality=(vtotal_deaths_cum/vTotalPop2010)*1000
lab var covidmortality "COVID deaths/thousand" 

gen vaxrate=vdaily_vaccinations_per_million
lab var vaxrate "Daily vaccinations/million"

lab var vAge65AndOlderPct2010 "% aged 65+"
lab var vAsianNonHispPct2010 "% Asian"
lab var vBlackNonHispPct2010 "% Black"
lab var vHispanicPct2010 "% Hispanic"
lab var vNatAmNonHispPct2010 "% Indigenous"

*low credit variables skewed - must use nonlinear transformation or polynomial
histogram paccept
histogram phesitancy
histogram lowcred
histogram vaxrate

gen loglowcred=log(.1+lowcred)
lab var loglowcred "Logged low credibility tweets"

histogram loglowcred
*slightly skewed at state level (check hettest)

*Descriptive statistics
sum phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop lowcred

*multivariate analyses

*Vaccine acceptance

*Empty model
reg phesitancy [aweight=awgt]


* Restricted models - low cred and gop vote 

reg phesitancy lowcred propgop [aweight=awgt]
estat ic
estimates store a1, title(Model a1)


* Full models - low cred and gop vote, plus all controls 

reg phesitancy lowcred propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality [aweight=awgt]
estat ic
estimates store a2, title(Model a2)

*Vaccination rate

*Empty model
reg vaxrate

* Restricted models - low cred and gop vote 

reg vaxrate lowcred propgop
estat ic
estimates store a3, title(Model a3)

* Full models - low cred and gop vote, plus all controls 

reg vaxrate lowcred propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality
estat ic
hettest
estimates store a4, title(Model a4)


esttab a* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table1SUP.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace










************* COUNTY LEVEL ANALYSES **************

clear

import excel "..\output_files\county_level_master_data--2021-04-16__22-10-10.xlsx", sheet("county_level_master_data--2021-") firstrow

rename value v

gen var = subinstr(variable," ","",.)

gen var2 = subinstr(var,"100_accounts","a100",.)
gen var3 = subinstr(var2,"50_accounts","a50",.)
gen var4 = subinstr(var3,"10_accounts","a10",.)
gen var5 = subinstr(var4,"1_accounts","a1",.)

gen var6 = subinstr(var5,"100_tweets","t100",.)
gen var7 = subinstr(var6,"50_tweets","t50",.)
gen var8 = subinstr(var7,"10_tweets","t10",.)
gen var9 = subinstr(var8,"1_tweets","t1",.)

gen var10 = subinstr(var9,".","",.)
gen var11 = subinstr(var10,"%","Pct",.)
gen var12 = subinstr(var11,"low-credibility","LC",.)

gen var13 = subinstr(var12,"accounts","Accounts",.)
gen var14 = subinstr(var13,"tweets","Tweets",.)
gen var15 = subinstr(var14,"NonHispanic","NonHisp",.)
gen var16 = subinstr(var15,"NativeAmerican","NatAm",.)
gen var17 = subinstr(var16, "mean_smoothed_covid_vaccinated_or_accept","AcceptVaccineMean",.)
gen var18 = subinstr(var17, "stderr_smoothed_covid_vaccinated_or_accept","AcceptVaccineStderr",.)
gen var19 = subinstr(var18, "Percentofadultswithabachelor'sdegreeorhigher,2015-19","PercBachelors",.)
gen var20 = subinstr(var19, "sample_size_for_covid_vaccinated_or_accept_question", "CovidSampleSize",.)
gen var21 = subinstr(var20, "num_smoothed_covid_vaccinated_or_accept", "CovidNum",.)


drop variable var-var20

rename var21 varshort

duplicates tag FIPS varshort, gen(dup)

fre dup

*There are two sets of values for eight counties - drop second instance 

duplicates drop FIPS var, force

drop dup


reshape wide v, i(FIPS) j(varshort) string

sum FIPS

drop if vAcceptVaccineMean==.

sum FIPS



*Add weights to account for DV standard errors

gen paccept=vAcceptVaccineMean*100
lab var paccept "% acceptance of vaccine"
gen pstderr=vAcceptVaccineStderr*100

gen phesitancy=100-paccept
lab var phesitancy "% hesitancy to get vaccine"

gen awgt=vCovidSampleSize

*focus on low cred versions with at least 10 accounts

gen lowcred100_1=va100_t1MeanPctLC
gen lowcred10_1=va10_t1MeanPctLC
gen lowcred50_1=va50_t1MeanPctLC

*drop those missing on key IV
drop if lowcred10_1==.

egen state=group(State)

gen gop=vprop_gop_vote
recode gop (0/.50=0)(.5000001/1=1)


gen propgop=10*vprop_gop_vote
lab var propgop "% GOP vote (10% change)"

gen ppoverty=(vPOVALL_2019/vTotalPop2010)*100
lab var ppoverty "% below poverty line"

gen population=vTotalPop2010/100000
lab var population "Population in 100,000's"


*Decide which covid rate variable to use
pwcorr phesitancy vrecent_cases_cum vrecent_deaths_cum vtotal_cases_cum vtotal_deaths_cum, sig
*Total deaths and total cases similar - keep total deaths for consistency with state

gen covidmortality=(vtotal_deaths_cum/vTotalPop2010)*1000
lab var covidmortality "COVID deaths/thousand" 

lab var vAge65AndOlderPct2010 "% aged 65+"
lab var vAsianNonHispPct2010 "% Asian"
lab var vBlackNonHispPct2010 "% Black"
lab var vHispanicPct2010 "% Hispanic"
lab var vNatAmNonHispPct2010 "% Indigenous"
lab var vRUCC_2013 "Rural-urban continuum code"


*Descriptive statistics
sum phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop lowcred100_1, d
fre vRUCC_2013



*low credit variables highly skewed - must use nonlinear transformation 
histogram paccept
histogram phesitancy
histogram lowcred100_1
histogram lowcred50_1
histogram lowcred10_1

*Scale of lowcred variable is super small, so adding 1 is inappropriately large, does not fix skew
*More appropriate to add .1, which is the same as adding 1 to 10*lowcred except latter has prettier (non-negative) x-axis

gen loglowcred100_1=log(.1+lowcred100_1)
gen loglowcred50_1=log(.1+lowcred50_1)
gen loglowcred10_1=log(.1+lowcred10_1)

histogram loglowcred100_1
histogram loglowcred50_1
histogram loglowcred10_1

egen stdlowcred100_1=std(lowcred100_1)
egen stdlowcred50_1=std(lowcred50_1)
egen stdlowcred10_1=std(lowcred10_1)



*Bivariate correlations between candidated covariates
pwcorr phesitancy loglowcred100_1 propgop covidmortality population vRUCC_2013 vMedHHInc vGini_Est ppoverty vPercBachelors vUnemployment_rate_2019 vTOTRATE vUnder18Pct2010 vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010, sig  
*RUCC codes better than population



*test for multicollinearity using state-level variables
reg phesitancy loglowcred100_1 propgop covidmortality vRUCC_2013 ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010
estat vif
*no multicollinearity


*test for heteroskedasticity
reg phesitancy loglowcred100_1 propgop [aweight=awgt]
hettest
*heteroskedasticity evident - need cluster robust standard errors


*multivariate analyses

*Empty model
reg phesitancy [aweight=awgt], cluster(state)


* Restricted models - low cred and gop vote (log)

reg phesitancy loglowcred100_1 propgop [aweight=awgt], cluster(state)
estat ic
estimates store c1, title(Model c1)

reg phesitancy loglowcred100_1 gop [aweight=awgt], cluster(state)
estat ic
estimates store c2, title(Model c2)

reg phesitancy c.loglowcred100_1##i.gop [aweight=awgt], cluster(state)
estat ic
estimates store c3, title(Model c3)

* Full models - low cred and gop vote, plus all controls (log)

reg phesitancy loglowcred100_1 propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store c4, title(Model c4)

reg phesitancy loglowcred100_1 gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store c5, title(Model c5)

reg phesitancy c.loglowcred100_1##i.gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)     
estat ic
estimates store c6, title(Model c6)


esttab c* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table3.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace





* Does GOP vote predict misinformation?

nbreg lowcred100_1 propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality, cluster(state) irr
estimates store d1, title(Model d1)

esttab d* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table4.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace


nbreg lowcred100_1 ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 propgop covidmortality, cluster(state) irr
margins, at(propgop=(2 3 4 5 6 7 8))
marginsplot



*FIGURES

*scatterplot
graph twoway (scatter phesitancy loglowcred100_1 if gop==0) (scatter phesitancy loglowcred100_1 if gop==1), ///
  legend(label(1 Dem) label(2 Rep)) 

*Logged graph

reg phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality c.loglowcred100_1##i.gop [aweight=awgt], cluster(state)
margins, at(loglowcred100_1=(-2.25 -2 -1.75 -1.5 -1.25 -1 -.75 -.5 -.25 0 .25 .5 .75)) over(gop)
marginsplot, name("accounts100log", replace) ytitle(Predicted value) yscale(range(0 35)) title("")
estat ic



*Sensitivity - adjusting for number of tweets in county

*low cred and gop vote + number of tweets [num tweets does not affect results for misinformation]

reg phesitancy loglowcred100_1 propgop va100_t1NoTweets [aweight=awgt], cluster(state)
estat ic

reg phesitancy loglowcred100_1 gop va100_t1NoTweets [aweight=awgt], cluster(state)
estat ic

reg phesitancy c.loglowcred100_1##i.gop va100_t1NoTweets [aweight=awgt], cluster(state)
estat ic


*Sensitivity - using smaller number of accounts, larger sample size [robust to different specifications]

* Restricted models - low cred and gop vote (log)

reg phesitancy loglowcred10_1 propgop [aweight=awgt], cluster(state)
estat ic
estimates store e1, title(Model e1)

reg phesitancy loglowcred50_1 propgop [aweight=awgt], cluster(state)
estat ic
estimates store f1, title(Model f1)

reg phesitancy loglowcred10_1 gop [aweight=awgt], cluster(state)
estat ic
estimates store e2, title(Model e2)

reg phesitancy loglowcred50_1 gop [aweight=awgt], cluster(state)
estat ic
estimates store f2, title(Model f2)

reg phesitancy c.loglowcred10_1##i.gop [aweight=awgt], cluster(state)
estat ic
estimates store e3, title(Model e3)

reg phesitancy c.loglowcred50_1##i.gop [aweight=awgt], cluster(state)
estat ic
estimates store f3, title(Model f3)

* Full models - low cred and gop vote, plus all controls (log)

reg phesitancy loglowcred10_1 propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store e4, title(Model e4)

reg phesitancy loglowcred10_1 gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store e5, title(Model e5)

reg phesitancy c.loglowcred10_1##i.gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)     
estat ic
estimates store e6, title(Model e6)

reg phesitancy loglowcred50_1 propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store f4, title(Model f4)

reg phesitancy loglowcred50_1 gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store f5, title(Model f5)

reg phesitancy c.loglowcred50_1##i.gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)     
estat ic
estimates store f6, title(Model f6)


esttab e* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table5.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace

esttab f* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table6.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace






*Sensitivity - original misinformation variable, no log [robust to different specifications]

* Restricted models - low cred and gop vote 

reg phesitancy lowcred100_1 propgop [aweight=awgt], cluster(state)
estat ic
estimates store g6, title(Model g6)

reg phesitancy lowcred100_1 gop [aweight=awgt], cluster(state)
estat ic
estimates store g6, title(Model g6)

reg phesitancy c.lowcred100_1##i.gop [aweight=awgt], cluster(state)
estat ic
estimates store g6, title(Model g6)

* Full models - low cred and gop vote, plus all controls 

reg phesitancy lowcred100_1 propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store g4, title(Model g4)

reg phesitancy lowcred100_1 gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store g5, title(Model g5)

reg phesitancy c.lowcred100_1##i.gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)     
estat ic
estimates store g6, title(Model g6)



esttab g* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table7.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace





*similar to logged version
reg phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality c.stdlowcred100_1##c.stdlowcred100_1##i.gop [aweight=awgt], cluster(state)
margins, at(stdlowcred100_1=(-2 -1 0 1 2 3)) over(gop)
marginsplot, ytitle(Predicted value) yscale(range(10 35)) title("")




keep state FIPS vRUCC_2013 paccept phesitancy ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 ///
vHispanicPct2010 vNatAmNonHispPct2010 covidmortality propgop loglowcred100_1 ///
loglowcred50_1 loglowcred10_1 lowcred100_1 lowcred50_1 lowcred100_1 gop awgt


export excel using "COUNTY_misinformation_clean-042221", replace firstrow(variables)






******************* COUNTY LEVEL ANALYSES WITH FILTERED KEY WORDS ***************




clear

import excel "..\output_files\county_level_keywords_filtered_master_data--2021-04-16__22-10-50.xlsx", sheet("county_level_keywords_filtered_") firstrow clear

rename value v

gen var = subinstr(variable," ","",.)

gen var2 = subinstr(var,"100_accounts","a100",.)
gen var3 = subinstr(var2,"50_accounts","a50",.)
gen var4 = subinstr(var3,"10_accounts","a10",.)
gen var5 = subinstr(var4,"1_accounts","a1",.)

gen var6 = subinstr(var5,"100_tweets","t100",.)
gen var7 = subinstr(var6,"50_tweets","t50",.)
gen var8 = subinstr(var7,"10_tweets","t10",.)
gen var9 = subinstr(var8,"1_tweets","t1",.)

gen var10 = subinstr(var9,".","",.)
gen var11 = subinstr(var10,"%","Pct",.)
gen var12 = subinstr(var11,"low-credibility","LC",.)

gen var13 = subinstr(var12,"accounts","Accounts",.)
gen var14 = subinstr(var13,"tweets","Tweets",.)
gen var15 = subinstr(var14,"NonHispanic","NonHisp",.)
gen var16 = subinstr(var15,"NativeAmerican","NatAm",.)
gen var17 = subinstr(var16, "mean_smoothed_covid_vaccinated_or_accept","AcceptVaccineMean",.)
gen var18 = subinstr(var17, "stderr_smoothed_covid_vaccinated_or_accept","AcceptVaccineStderr",.)
gen var19 = subinstr(var18, "Percentofadultswithabachelor'sdegreeorhigher,2015-19","PercBachelors",.)
gen var20 = subinstr(var19, "sample_size_for_covid_vaccinated_or_accept_question", "CovidSampleSize",.)
gen var21 = subinstr(var20, "num_smoothed_covid_vaccinated_or_accept", "CovidNum",.)


drop variable var-var20

rename var21 varshort

duplicates tag FIPS varshort, gen(dup)

fre dup

*There are two sets of values for eight counties - drop second instance 

duplicates drop FIPS var, force

drop dup


reshape wide v, i(FIPS) j(varshort) string

sum FIPS

drop if vAcceptVaccineMean==.

sum FIPS



*Add weights to account for DV standard errors

gen paccept=vAcceptVaccineMean*100
lab var paccept "% acceptance of vaccine"
gen pstderr=vAcceptVaccineStderr*100

gen phesitancy=100-paccept
lab var phesitancy "% hesitancy to get vaccine"

gen awgt=vCovidSampleSize

*focus on low cred versions with at least 10 accounts

gen lowcred100_1=va100_t1MeanPctLC
gen lowcred10_1=va10_t1MeanPctLC
gen lowcred50_1=va50_t1MeanPctLC

*drop those missing on key IV
drop if lowcred10_1==.

egen state=group(State)

gen gop=vprop_gop_vote
recode gop (0/.50=0)(.5000001/1=1)


gen propgop=10*vprop_gop_vote
lab var propgop "% GOP vote (10% change)"

gen ppoverty=(vPOVALL_2019/vTotalPop2010)*100
lab var ppoverty "% below poverty line"

gen population=vTotalPop2010/100000
lab var population "Population in 100,000's"

gen covidmortality=(vtotal_deaths_cum/vTotalPop2010)*1000
lab var covidmortality "COVID deaths/thousand" 

lab var vAge65AndOlderPct2010 "% aged 65+"
lab var vAsianNonHispPct2010 "% Asian"
lab var vBlackNonHispPct2010 "% Black"
lab var vHispanicPct2010 "% Hispanic"
lab var vNatAmNonHispPct2010 "% Indigenous"
lab var vRUCC_2013 "Rural-urban continuum code"


*low credit variables highly skewed - must use nonlinear transformation 
histogram paccept
histogram phesitancy
histogram lowcred100_1
histogram lowcred50_1
histogram lowcred10_1

gen loglowcred100_1=log(.1+lowcred100_1)
gen loglowcred50_1=log(.1+lowcred50_1)
gen loglowcred10_1=log(.1+lowcred10_1)

histogram loglowcred100_1
histogram loglowcred50_1
histogram loglowcred10_1





*multivariate analyses

*Empty model
reg phesitancy [aweight=awgt], cluster(state)


* Restricted models - low cred and gop vote (log)

reg phesitancy loglowcred100_1 propgop [aweight=awgt], cluster(state)
estat ic
estimates store c1, title(Model c1)

reg phesitancy loglowcred100_1 gop [aweight=awgt], cluster(state)
estat ic
estimates store c2, title(Model c2)

reg phesitancy c.loglowcred100_1##i.gop [aweight=awgt], cluster(state)
estat ic
estimates store c3, title(Model c3)

* Full models - low cred and gop vote, plus all controls (log)

reg phesitancy loglowcred100_1 propgop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store c4, title(Model c4)

reg phesitancy loglowcred100_1 gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)
estat ic
estimates store c5, title(Model c5)

reg phesitancy c.loglowcred100_1##i.gop ppoverty vAge65AndOlderPct2010 vAsianNonHispPct2010 vBlackNonHispPct2010 vHispanicPct2010 vNatAmNonHispPct2010 vRUCC_2013 covidmortality [aweight=awgt], cluster(state)     
estat ic
estimates store c6, title(Model c6)


esttab c* using "C:\Users\blperry\OneDrive - Indiana University\BREA\1. Research\Other Projects\Table3SUP.rtf", ///
cells(b(star fmt(3)) se(par fmt(2))) stats(r2 bic N, star) legend label varlabels(_cons Constant) replace








log close




















