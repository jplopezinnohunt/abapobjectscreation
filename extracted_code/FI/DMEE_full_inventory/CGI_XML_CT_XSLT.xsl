<?xml version="1.0" encoding="utf-8"?>
<!--
  CGI_XML_CT_XSLT — SAP-standard XSLT post-processor
  devclass: ID-DMEE | author: SAP | source: SAP

  Used by (verified DMEE_TREE_HEAD.XSLTDESC field 2026-04-25):
  - /CITI/XML/UNESCO/DC_V3_01     ✅ uses this XSLT
  - /SEPA_CT_UNES                  ❌ no XSLT
  - /CGI_XML_CT_UNESCO             ❌ no XSLT
  - /CGI_XML_CT_UNESCO_1           ❌ no XSLT

  Behavior: identity transformation with empty-element removal.
  - Template 1 (line 4): match any element with no child nodes (no text, no children) → delete
  - Template 2 (lines 6-11): match elements with string content OR attributes with values → copy

  Effect for CITI V001 design:
  - Tree can emit ALL 5 structured PstlAdr nodes unconditionally
  - XSLT auto-removes empty ones (e.g., <BldgNb/> when vendor missing HOUSE_NUM1)
  - Vendors with only CITY1+COUNTRY → output naturally collapses to TwnNm+Ctry (CBPR+ Hybrid-minimum valid)

  Effect for SEPA + CGI V001 design (NO XSLT applies):
  - Empty structured nodes WILL be emitted unless explicit DMEE_TREE_COND suppresses them
  - Need to add COND rules per node: emit only if source field IS NOT INITIAL

  Source extracted via user screenshot from P01 STRANS Tx 2026-04-25
  (RPY_PROGRAM_READ blocked for XSLT objects)
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output indent="no" method="xml" omit-xml-declaration="yes"/>

  <xsl:template match="*[not(child::node())]"/>

  <xsl:template match="*[string() or @*[string()]]">
    <xsl:copy>
      <xsl:copy-of select="@*[string()]"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
