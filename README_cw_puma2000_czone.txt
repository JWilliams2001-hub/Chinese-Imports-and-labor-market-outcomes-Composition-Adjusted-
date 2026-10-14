README for crosswalk file cw_puma2000_czone.dta
David Dorn
Updated Sept. 2026 with clarification on use with ACS 2006-2011 data

Notes:
The original crosswalk by Autor and Dorn (2013) was created for use with Census 2000 and ACS 2005 data. Create a variable "puma2000" whose first two digits are the state FIPS code and whose last four digits are the PUMA code within a state (note that some newer data files report the PUMA code within a state with five digits, the first of which is a leading zero that can be dropped). Use the Stata command "joinby" to combine the Census microdata with the crosswalk file using the variable "puma2000". The variable "afactor" in the crosswalk indicates which fraction of a PUMA's population maps to a given CZ. To analyze weighted Census data, the person weight from the Census needs to be multiplied with "afactor".

Use with ACS 2006-2011: 
Following hurricane Katrina in August 2005, the US Census Bureau merged the Louisiana PUMAs 1801, 1802, and 1905 to form a new PUMA 77777 in the 2006–2011 ACS because their populations had become too small to be identified separately. The three Louisiana PUMAs that were combined into PUMA 77777 all map to the same commuting zone CZ 3300. One can apply the crosswalk to ACS 2006-11 data after replacing the PUMA code 77777 with code 1801, such that the crosswalk subsequently matches the PUMA to the correct CZ 3300.

Suggested Stata code:
replace puma=1801 if puma==77777
gen puma2000=(statefip*10000)+puma
sort puma2000
joinby puma2000 using cw_puma2000_czone.dta


Please cite as source for this file:
David Autor and David Dorn. "The Growth of Low Skill Service Jobs and the Polarization of the U.S. Labor Market." American Economic Review, 103(5), 1553-1597, 2013.