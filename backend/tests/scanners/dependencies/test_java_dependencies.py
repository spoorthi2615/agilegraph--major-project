from src.scanners.dependencies.scanner import scan_manifest

def test_parse_pom_xml():
    content = """<project>
      <dependencies>
        <dependency>
          <groupId>org.bouncycastle</groupId>
          <artifactId>bcprov-jdk15on</artifactId>
          <version>1.68</version>
        </dependency>
      </dependencies>
    </project>"""
    records = scan_manifest("repo", "pom.xml", content)
    assert len(records) == 1
    assert records[0].package_name == "org.bouncycastle:bcprov-jdk15on"
    assert records[0].version == "1.68"
    assert records[0].ecosystem == "maven"
    assert records[0].crypto_relevance == "CRYPTOGRAPHIC"
