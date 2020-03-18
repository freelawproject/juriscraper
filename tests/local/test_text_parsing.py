# -*- coding: utf-8 -*-

import unittest
from juriscraper.opinions.united_states.federal_special import tax


class TextExtraction(unittest.TestCase):
    def test_tax_court_citation_extractor(self):
        """Find Tax Court Citations  """

        test_pairs = (
            (
                """  1 UNITED STATES TAX COURT REPORT (2018)



                     UNITED STATES TAX COURT



 BENTLEY COURT II LIMITED PARTNERSHIP, B.F. BENTLEY, INC., TAX
                 MATTERS PARTNER, Petitioner v.
          COMMISSIONER OF INTERNAL REVENUE, Respondent



     Docket No. 5393-04.                Filed May 31, 2006.



     Nancy Ortmeyer Kuhn, for petitioner.
        """,
                "1 T.C. 2018",
            ),
            (
                """  T.C. Memo. 2003-150



                                  UNITED STATES TAX COURT



                       RIVER CITY RANCHES #1 LTD., LEON SHEPARD,
                                  TAX MATTERS PARTNER,
                       RIVER CITY RANCHES #2 LTD., LEON SHEPARD,
                                   TAX MATTERS PARTNER,
                        RIVER CITY RANCHES #3 LTD., LEON SHEPARD,
                                   TAX MATTERS PARTNER,


                """,
                "2003 T.C. Memo. 150",
            ),
            (
                """  T.C. Summary Opinion 2003-150



                                  UNITED STATES TAX COURT



                       RIVER CITY RANCHES #1 LTD., LEON SHEPARD,
                                  TAX MATTERS PARTNER,
                       RIVER CITY RANCHES #2 LTD., LEON SHEPARD,
                                   TAX MATTERS PARTNER,
                        RIVER CITY RANCHES #3 LTD., LEON SHEPARD,
                                   TAX MATTERS PARTNER,


                """,
                "2003 T.C. Summary Opinion 150",
            ),
            (
                """
                   MICHAEL KEITH SHENK, PETITIONER v. COMMISSIONER
                                                    OF INTERNAL REVENUE, RESPONDENT

                                                        Docket No. 5706–12.                            Filed May 6, 2013.

                                                  P was divorced from his wife, and their 2003 ‘‘Judgment of
                                               Absolute Divorce’’ provided that his ex-wife would have pri-
                                               mary residential custody of their three minor children. The
                                               judgment provided that the dependency exemption deductions
                                               for the three children would be divided between the two ex-
                                               spouses according to various conditions but did not provide
                                               that the ex-wife must execute in P’s favor a Form 8332,
                                               ‘‘Release of Claim to Exemption for Child of Divorced or Sepa-
                                               rated Parents’’. The children resided with P’s ex-wife for more
                                               than half of 2009, and P’s ex-wife did not execute in P’s favor
                                               any Form 8332 or equivalent document for any year. For 2009
                                               P timely filed a Federal income tax return on which he
                                               claimed dependency exemption deductions and the child tax
                                               credit for two of the children, consistent with his under-
                                               standing of the terms of the judgment, but he did not attach
                                               any Form 8332 to his return. He also claimed head-of-house-
                                               hold filing status. His ex-wife, the custodial parent, timely
                                               filed a Federal income tax return for 2009 on which she also

                                      200




VerDate Nov 24 2008   10:59 Jul 11, 2014   Jkt 372897    PO 20012   Frm 00001   Fmt 3857   Sfmt 3857   V:\FILES\BOUND VOL. WITHOUT CROP MARKS\B.V.140\SHENK   JAMIE
                                      (200)                          SHENK v. COMMISSIONER                                        201


                                               claimed two dependency exemption deductions, so that one
                                               child was claimed on both parents’ returns. R allowed to P the
                                               dependency exemption deduction for one of the children but
                                               disallowed his claim for the dependency exemption deduction
                                               for the child who had also been claimed by the custodial
                                               parent. At trial P contended he is entitled to a dependency
                                               exemption deduction for all three children. Held: Since the
                                               custodial parent did not execute, and P could not and did not
                                               attach to his return, any Form 8332 or equivalent release, P
                                               is not entitled under I.R.C. sec. 152(e)(2)(A) to claim the
                                               dependency exemption deduction or the child tax credit. Held,
                                               further, where both the custodial parent and the noncustodial
                                               parent have claimed for the same year a dependency exemp-
                                               tion deduction for the same child, a declaration signed by the
                                               custodial parent after the period of limitations for assess-
                                               ments has expired as to the custodial parent could not qualify
                                               under I.R.C. sec. 152(e)(2)(A), and therefore there is no reason
                                               to grant P’s request to leave the record open so that he may
                                               obtain and proffer such a declaration. Held, further, P is not
                                               entitled to head-of-household filing status under I.R.C. sec.
                                               2(b)(1) nor to the child tax credit under I.R.C. sec. 24.

                                           Michael Keith Shenk, for himself.
                                           Shari Salu, for respondent.
                                         GUSTAFSON, Judge: The Internal Revenue Service (IRS)
                                      determined a deficiency of $3,136 in the 2009 Federal income
                                      tax of petitioner Michael Keith Shenk. Mr. Shenk petitioned
                                      this Court, pursuant to section 6213(a), 1 for redetermination
                                      of the deficiency. After Mr. Shenk’s concession that he
                                      received but did not report $254 in dividend income, the
                                      issue for decision is whether Mr. Shenk is entitled to a
                                      dependency exemption deduction for one of his children
                                      under section 151(c), a child tax credit for that child under
                                      section 24(a), and head-of-household filing status under sec-
                                      tion 2(b)(1). On these issues, we hold for the IRS.
                                                                          FINDINGS OF FACT

                                      The judgment of divorce
                                        Mr. Shenk was married to Julie Phillips, and they have
                                      three minor children—M.S., W.S., and L.S. They divorced in
                                      2003. The family court’s ‘‘Judgment of Absolute Divorce’’ pro-
                                         1 Unless otherwise indicated, all citations of sections refer to the Internal

                                      Revenue Code (26 U.S.C.) in effect for the tax year at issue, and all cita-
                                      tions of Rules refer to the Tax Court Rules of Practice and Procedure.




VerDate Nov 24 2008   10:59 Jul 11, 2014   Jkt 372897   PO 20012   Frm 00002   Fmt 3857   Sfmt 3857   V:\FILES\BOUND VOL. WITHOUT CROP MARKS\B.V.140\SHENK   JAMIE
                                      202                 140 UNITED STATES TAX COURT REPORTS                                   (200)


                                      vided: that Ms. Phillips was ‘‘awarded primary residential
                                      custody’’ of the parties’ three children; and that Mr. Shenk
                                      would be liable for child support payments; but that, as to
                                      dependency exemptions—""",
                "140 T.C. 200",
            ),
        )
        site = tax.Site()
        for q, a in test_pairs:
            results = site.extract_from_text(q)
            cite_string = "%s %s %s" % (
                results["Citation"]["volume"],
                results["Citation"]["reporter"],
                results["Citation"]["page"],
            )

            self.assertEqual(cite_string, a)
            print "✓", cite_string

    def test_tax_court_docket_number_extractor(self):
        """Test Docket Numbers extraction from opinions"""

        test_pairs = (
            (
                """  1 UNITED STATES TAX COURT REPORT (2018)
    
    
    
                     UNITED STATES TAX COURT
    
    
    
    BENTLEY COURT II LIMITED PARTNERSHIP, B.F. BENTLEY, INC., TAX
                 MATTERS PARTNER, Petitioner v.
          COMMISSIONER OF INTERNAL REVENUE, Respondent
    
    
    
     Docket No. 5393-04.                Filed May 31, 2006.
    
    
    
     Nancy Ortmeyer Kuhn, for petitioner.
        """,
                "5393-04",
            ),
            (
                """
                   MICHAEL KEITH SHENK, PETITIONER v. COMMISSIONER
                                                    OF INTERNAL REVENUE, RESPONDENT
    
                                                        Docket No. 5706–12.                            Filed May 6, 2013.
    
                                                  P was divorced from his wife, and their 2003 ‘‘Judgment of
                                               Absolute Divorce’’ provided that his ex-wife would have pri-
                                               mary residential custody of their three minor children. The
                                               judgment provided that the dependency exemption deductions
                                               for the three children would be divided between the two ex-
                                               spouses according to various conditions but did not provide
                                               that the ex-wife must execute in P’s favor a Form 8332,
                                               ‘‘Release of Claim to Exemption for Child of Divorced or Sepa-
                                               rated Parents’’. The children resided with P’s ex-wife for more
                                               than half of 2009, and P’s ex-wife did not execute in P’s favor
                                               any Form 8332 or equivalent document for any year. For 2009
                                               P timely filed a Federal income tax return on which he
                                               claimed dependency exemption deductions and the child tax
                                               credit for two of the children, consistent with his under-
                                               standing of the terms of the judgment, but he did not attach
                                               any Form 8332 to his return. He also claimed head-of-house-
                                               hold filing status. His ex-wife, the custodial parent, timely
                                               filed a Federal income tax return for 2009 on which she also
    
                                      200
    
    
    
    
    VerDate Nov 24 2008   10:59 Jul 11, 2014   Jkt 372897    PO 20012   Frm 00001   Fmt 3857   Sfmt 3857   V:\FILES\BOUND VOL. WITHOUT CROP MARKS\B.V.140\SHENK   JAMIE
                                          (200)                          SHENK v. COMMISSIONER                                        201
    
    
                                               claimed two dependency exemption deductions, so that one
                                               child was claimed on both parents’ returns. R allowed to P the
                                               dependency exemption deduction for one of the children but
                                               disallowed his claim for the dependency exemption deduction
                                               for the child who had also been claimed by the custodial
                                               parent. At trial P contended he is entitled to a dependency
                                               exemption deduction for all three children. Held: Since the
                                               custodial parent did not execute, and P could not and did not
                                               attach to his return, any Form 8332 or equivalent release, P
                                               is not entitled under I.R.C. sec. 152(e)(2)(A) to claim the
                                               dependency exemption deduction or the child tax credit. Held,
                                               further, where both the custodial parent and the noncustodial
                                               parent have claimed for the same year a dependency exemp-
                                               tion deduction for the same child, a declaration signed by the
                                               custodial parent after the period of limitations for assess-
                                               ments has expired as to the custodial parent could not qualify
                                               under I.R.C. sec. 152(e)(2)(A), and therefore there is no reason
                                               to grant P’s request to leave the record open so that he may
                                               obtain and proffer such a declaration. Held, further, P is not
                                               entitled to head-of-household filing status under I.R.C. sec.
                                               2(b)(1) nor to the child tax credit under I.R.C. sec. 24.
    
                                           Michael Keith Shenk, for himself.
                                           Shari Salu, for respondent.
                                         GUSTAFSON, Judge: The Internal Revenue Service (IRS)
                                      determined a deficiency of $3,136 in the 2009 Federal income
                                      tax of petitioner Michael Keith Shenk. Mr. Shenk petitioned
                                      this Court, pursuant to section 6213(a), 1 for redetermination
                                      of the deficiency. After Mr. Shenk’s concession that he
                                      received but did not report $254 in dividend income, the
                                      issue for decision is whether Mr. Shenk is entitled to a
                                      dependency exemption deduction for one of his children
                                      under section 151(c), a child tax credit for that child under
                                      section 24(a), and head-of-household filing status under sec-
                                      tion 2(b)(1). On these issues, we hold for the IRS.
                                                                          FINDINGS OF FACT
    
                                      The judgment of divorce
                                        Mr. Shenk was married to Julie Phillips, and they have
                                      three minor children—M.S., W.S., and L.S. They divorced in
                                      2003. The family court’s ‘‘Judgment of Absolute Divorce’’ pro-
                                         1 Unless otherwise indicated, all citations of sections refer to the Internal
    
                                      Revenue Code (26 U.S.C.) in effect for the tax year at issue, and all cita-
                                      tions of Rules refer to the Tax Court Rules of Practice and Procedure.
    
    
    
    
    VerDate Nov 24 2008   10:59 Jul 11, 2014   Jkt 372897   PO 20012   Frm 00002   Fmt 3857   Sfmt 3857   V:\FILES\BOUND VOL. WITHOUT CROP MARKS\B.V.140\SHENK   JAMIE
                                          202                 140 UNITED STATES TAX COURT REPORTS                                   (200)
    
    
                                      vided: that Ms. Phillips was ‘‘awarded primary residential
                                      custody’’ of the parties’ three children; and that Mr. Shenk
                                      would be liable for child support payments; but that, as to
                                      dependency exemptions—""",
                "5706-12",
            ),
        )
        site = tax.Site()
        for q, a in test_pairs:
            results = site.extract_from_text(q)
            cite_string = "%s %s %s" % (
                results["Citation"]["volume"],
                results["Citation"]["reporter"],
                results["Citation"]["page"],
            )
            docket_number = results['Docket']['docket_number']
            self.assertEqual(docket_number, a)
            print "✓", docket_number

