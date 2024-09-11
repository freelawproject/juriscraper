str = "U.S. Court of Appeals Case No:  22-2884 U.S. District Court for the District of South Dakota - Western [UNPUBLISHED] [Per Curiam - Before Benton, Erickson, and Kobes, Circuit Judges] Criminal case - Sentencing. Whether defendant's above-Guidelines range sentence was a departure or variance, the district court did not abuse its discretion by relying on conduct "
txt = str.split("]")[1].replace("[", "").strip()
print(txt)
