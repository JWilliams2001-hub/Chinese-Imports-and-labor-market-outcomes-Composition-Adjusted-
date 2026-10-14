
cd "/Users/jvogel/Library/CloudStorage/Dropbox/Teaching/UCLA MA/Lectures/Assignments/Assignment 1/ADH_replication/dta/"

* Bring in ADH replication data set
use  "workfile_china.dta", clear


/* The following code starts from the ADH replication data set.
It conducts three exercises:
1) Use only 1990-2000 changes (do not stack time periods)
2) Use only 2000-2007 changes (do not stack time periods)
3) Stack time periods and separately:
	a) replicate ADH 
	b) include time-varying impact of 1990 manufacturing share
	
The question we are after is: Are these results robust? Specifically
A) Are the average results across time periods similar to baseline? i.e., perhaps stacking just buys precision.
B) When we stack time periods but control more flexibly for effect of manufacturing share, do results hold?

You must construct your own tables and choose how best to present these results	
*/

******************************
* Do not stack periods I: 1990-2000
******************************

***************TABLE 5 Panel B

** Manufacturing share

ivregress 2sls d_sh_empl_mfg (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==1990, cluster(statefip)

** Non-manufacturing share

ivregress 2sls d_sh_empl_nmfg (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==1990, cluster(statefip)

** Unemployment

ivregress 2sls d_sh_unempl (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==1990, cluster(statefip)

** NILF

ivregress 2sls d_sh_nilf (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==1990, cluster(statefip)

***************TABLE 6 Top Left Result Only: All workers

* log weekly wage

ivregress 2sls d_avg_lnwkwage (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==1990, cluster(statefip)




******************************
* Do not stack periods II: 2000-2007
******************************

***************TABLE 5 Panel B

** Manufacturing share

ivregress 2sls d_sh_empl_mfg (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==2000, cluster(statefip)

** Non-manufacturing share

ivregress 2sls d_sh_empl_nmfg (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==2000, cluster(statefip)

** Unemployment

ivregress 2sls d_sh_unempl (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==2000, cluster(statefip)

** NILF

ivregress 2sls d_sh_nilf (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==2000, cluster(statefip)

***************TABLE 6 Top Left Result Only: All workers

* log weekly wage

ivregress 2sls d_avg_lnwkwage (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* [aw=timepwt48] if yr==2000, cluster(statefip)



******************************
* Include time-varying effect of 1990 manufacturing share
******************************

* define the 1990 manufacturing share of the CZ within each observation

bys cz: egen mshare90=max( l_shind_manuf_cbp*(yr==1990))


***************TABLE 5 Panel B

** Manufacturing share

* their manufacturing share specication
ivregress 2sls d_sh_empl_mfg (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* t2 [aw=timepwt48], cluster(statefip)

* including time-varying effect of lagged manufacturing share
ivregress 2sls d_sh_empl_mfg (d_tradeusch_pw=d_tradeotch_pw_lag) i.yr#c.mshare90 l_shind_manuf_cbp reg* l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource t2 [aw=timepwt48], cluster(statefip)

** Non-manufacturing share

* their non-manufacturing share specication
ivregress 2sls d_sh_empl_nmfg (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* t2 [aw=timepwt48], cluster(statefip)

* including time-varying effect of lagged manufacturing share
ivregress 2sls d_sh_empl_nmfg (d_tradeusch_pw=d_tradeotch_pw_lag) i.yr#c.mshare90 l_shind_manuf_cbp reg* l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource t2 [aw=timepwt48], cluster(statefip)

** Unemployment

* their unemployment share specication
ivregress 2sls d_sh_unempl (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* t2 [aw=timepwt48], cluster(statefip)

* including time-varying effect of lagged manufacturing share
ivregress 2sls d_sh_unempl (d_tradeusch_pw=d_tradeotch_pw_lag) i.yr#c.mshare90 l_shind_manuf_cbp reg* l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource t2 [aw=timepwt48], cluster(statefip)

** NILF

* their NILF share specication
ivregress 2sls d_sh_nilf (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* t2 [aw=timepwt48], cluster(statefip)

* including time-varying effect of lagged manufacturing share
ivregress 2sls d_sh_nilf (d_tradeusch_pw=d_tradeotch_pw_lag) i.yr#c.mshare90 l_shind_manuf_cbp reg* l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource t2 [aw=timepwt48], cluster(statefip)

***************TABLE 6 Top Left Result Only: All workers

* their log weekly wage specication
ivregress 2sls d_avg_lnwkwage (d_tradeusch_pw=d_tradeotch_pw_lag) l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* t2 [aw=timepwt48], cluster(statefip)

* including time-varying effect of lagged manufacturing share
ivregress 2sls d_avg_lnwkwage (d_tradeusch_pw=d_tradeotch_pw_lag) i.yr#c.mshare90 l_shind_manuf_cbp l_sh_popedu_c l_sh_popfborn l_sh_empl_f l_sh_routine33 l_task_outsource reg* t2 [aw=timepwt48], cluster(statefip)

