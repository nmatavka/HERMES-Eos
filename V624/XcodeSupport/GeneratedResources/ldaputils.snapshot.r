data 'STR#' (32767, "LDAP attr table") {
	$"001E 0243 4E04 4E61 6D65 0A43 6F6D 6D6F"            /* ...CN.Name.Commo */
	$"6E4E 616D 6504 4E61 6D65 014C 0443 6974"            /* nName.Name.L.Cit */
	$"7902 5354 0553 7461 7465 014F 0C4F 7267"            /* y.ST.State.O.Org */
	$"616E 697A 6174 696F 6E02 4F55 134F 7267"            /* anization.OU.Org */
	$"616E 697A 6174 696F 6E61 6C20 756E 6974"            /* anizational unit */
	$"0143 0743 6F75 6E74 7279 0653 5452 4545"            /* .C.Country.STREE */
	$"540E 5374 7265 6574 2061 6464 7265 7373"            /* T.Street address */
	$"046D 6169 6C06 452D 6D61 696C 076D 6169"            /* .mail.E-mail.mai */
	$"6C62 6F78 0645 2D6D 6169 6C0D 7266 6338"            /* lbox.E-mail.rfc8 */
	$"3232 4D61 696C 626F 7806 452D 6D61 696C"            /* 22Mailbox.E-mail */
	$"0253 4E09 4C61 7374 206E 616D 6509 6769"            /* .SN.Last name.gi */
	$"7665 6E6E 616D 650A 4769 7665 6E20 6E61"            /* venname.Given na */
	$"6D65 0A6C 6162 656C 6564 5552 490A 5765"            /* me.labeledURI.We */
	$"6220 6C6F 6F6B 7570 0F74 656C 6570 686F"            /* b lookup.telepho */
	$"6E65 4E75 6D62 6572 0954 656C 6570 686F"            /* neNumber.Telepho */
	$"6E65"                                               /* ne */
};
data 'TEXT' (32767, "LDAP server list", purgeable) {
	$"4C44 4150 2073 6572 7665 7273 3A0D 0D3C"            /* LDAP servers:..< */
	$"6C64 6170 3A2F 2F6C 6461 702E 6269 6766"            /* ldap://ldap.bigf */
	$"6F6F 742E 636F 6D2F 3E0D"                           /* oot.com/>. */
};
data 'FUtf' (128, "ldap.bigfoot.com", purgeable) {
	$"00"                                                 /* . */
};
data 'FUtf' (129, "ldap.four11.com", purgeable) {
	$"00"                                                 /* . */
};
data 'FUcf' (128, "ldap.bigfoot.com", purgeable) {
	$"0928 636E 3D2A 5E30 2A29"                           /* .(cn=*^0*) */
};
data 'FUcf' (129, "ldap.four11.com", purgeable) {
	$"0928 636E 3D2A 5E30 2A29"                           /* .(cn=*^0*) */
};
data 'TGMP' (128, "Ph", purgeable) {
	$"0250 6800 0008 0561 6C69 6173 0565 6D61"            /* .Ph....alias.ema */
	$"696C 0570 686F 6E65 0570 686F 6E65 0C68"            /* il.phone.phone.h */
	$"6F6D 655F 6164 6472 6573 7307 6164 6472"            /* ome_address.addr */
	$"6573 7303 6661 7803 6661 7805 7469 746C"            /* ess.fax.fax.titl */
	$"6505 7469 746C 650A 6365 6C6C 5F70 686F"            /* e.title.cell_pho */
	$"6E65 066D 6F62 696C 6509 686F 6D65 5F70"            /* ne.mobile.home_p */
	$"6167 6503 7765 620E 6F66 6669 6365 5F61"            /* age.web.office_a */
	$"6464 7265 7373 0861 6464 7265 7373 32"              /* ddress.address2 */
};
