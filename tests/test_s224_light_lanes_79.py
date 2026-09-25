"""s224 w1: the light lanes record, the eightieth file.

Ground truth measured 2026-09-22 (solo):

- the eighty guards re-ran green solo: 162 passed, rc 0,
  /tmp/s224-w1-guards.log (80 files. The brief's 71-file list plus
  the s214, s216, s217, s218, s219, s220, s221, s222, and s223 records,
  which joined the set).
- one bounded route probe re-confirmed the serve table: the pinned
  glm route call (.rumpun/rumpun.yaml line 38), --model glm-5.3
  (the s125 through s223 season precedent), one call, rc 0,
  stdout reply `ok` (3 bytes). The stderr carried the known catalog
  warning (CLI-side text, the s125 classification, 788 bytes,
  byte-identical to the s223 stderr, cmp rc 0).
  Trail: /tmp/s224-w1-probe.out and /tmp/s224-w1-probe.err (prompt:
  /tmp/s224-w1-probe-prompt.txt, rc: /tmp/s224-w1-probe.rc).
- drift: none on the guards. All 79 guards shared with the s223 sweep
  are byte-identical (fresh sha256 each, compared against the rows in
  tests/test_s223_light_lanes_78.py). The s223 record joined the
  guards at ea8b61b07439e19ae2944b40b2dbf43a5c3e0624a3eeb27868a4b563aea5c6e9.
- one naming drift, named: the brief's stated target path
  (tests/test_s214_light_lanes_70.py) is occupied (the seed template
  froze at s214 and light-lanes-70). This record takes the next free
  name (tests/test_s224_light_lanes_79.py). A landed record does not
  get overwritten.

The record: the guards' versions (sha256 of each guard file's
bytes), the probe result, the sweep date. Reads only: no network,
no writes.

A red on the versions pin means a guard moved since this sweep. The
next steady-state cycle re-runs the guard and refreshes the record.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

SWEEP_DATE = "2026-09-22"
GUARD_VERSIONS = {
    "tests/test_s136_full_guide_lint.py":
        "208e9054eedc61cc7d590d99caf5fbc50821ccc81d8d793e81d7fbd36a77642e",
    "tests/test_s128_readme_verbs_lint.py":
        "5795fa17b6831697116554833514f41547b42d3642ef1da183c28051b2bc1378",
    "tests/test_s136_route_probes.py":
        "9ecd825b54025199a8f308d7ff5ea580bd31763f96bc71d059b4eb48f4ccef02",
    "tests/test_s139_light_lanes_sweep.py":
        "a329b1d9a30884e986e80ab32d48faac165b806cfec8ce5467909ec76ad13539",
    "tests/test_s140_steady_sweep_2.py":
        "0bae2fc3e78f11ff4ac6c70da6bd0dcffbf0be8c2ea23cf26b2d3b0a74fab26a",
    "tests/test_s147_light_lanes_3.py":
        "9992877f3ecfb6028ca2bffb40ba32f9add4af3ccdad2cf7dda13ce2b5e9cc14",
    "tests/test_s148_light_lanes_4.py":
        "d24a5c5688562be620305dc0b884b5311971535736ace2282b8e898060f54912",
    "tests/test_s149_light_lanes_5.py":
        "fe40794b7d93b152123c33dad44ec3aeccd83298e5a2203574424e3bc0029554",
    "tests/test_s150_light_lanes_6.py":
        "be4bd73a28df1cb74f62087b86d77dfc304b3d05e9e01b6412796ac193595be6",
    "tests/test_s152_light_lanes_8.py":
        "d691c2f7e16ff87a06d44365771c9246a8c47ab68712ef713eeb658f713b1590",
    "tests/test_s153_light_lanes_9.py":
        "9592e9c244ed8328d06cbad3e4ebd0c36546f203ddcf0d4e1701570de7c1b786",
    "tests/test_s154_light_lanes_10.py":
        "70da5afea95c628a4f73f6cf0fa25c17776cfc444ad37ee143a009a4f1b6a9b3",
    "tests/test_s155_light_lanes_11.py":
        "35590aa85b5c2dd9c948c7ebd9b183194fda2e1c4546fbc1e070ce9d95abada2",
    "tests/test_s156_light_lanes_12.py":
        "dc243d25d70502e0f45ca5a553da0e06f52a489943fdfc6e5875ab54cf96b613",
    "tests/test_s157_light_lanes_13.py":
        "b50cdb9bb01880334211ad9ddf68f6fefd3f34d134f5f443f6cebe3ba260dbcb",
    "tests/test_s158_light_lanes_14.py":
        "4bcb6e8ac8e9814192feeaf3cda04866cdc3d295716e92dddfa0199ae416678c",
    "tests/test_s159_light_lanes_15.py":
        "b5a395943c69039c9b3a73c23d580f2926a5b6e5b13426c18f24ee8e849f4d7f",
    "tests/test_s160_light_lanes_16.py":
        "dd804828429bea869d997725b285fd9447ce24544970f67cbd6459b5cebbc6ff",
    "tests/test_s161_light_lanes_17.py":
        "9c11fc5ca902b8bf4461b25721e793854de769f1d17632f62b6aac6f54c3bd90",
    "tests/test_s162_light_lanes_18.py":
        "566b094e86c868adf74d01c6ce941976fa88b6806b0794ed411a5ef21283712f",
    "tests/test_s163_light_lanes_19.py":
        "11ba35d7547b714c187d79d4624f95fd98713d0b706f558ac8b59db35c8c5afd",
    "tests/test_s164_light_lanes_20.py":
        "ace442c3a395ff0dd6d1cc1d58a62cc59f818a2609df1e5d1dba4e86509c3a27",
    "tests/test_s165_light_lanes_21.py":
        "e703a22945c0d3a365d462c18a9e544659d82bd876320044a8206b339d80ab16",
    "tests/test_s166_light_lanes_22.py":
        "cb9ec237a77dadc7f709ce97d7d6a78579863de0959f5a12bbc58176e799f07e",
    "tests/test_s167_light_lanes_23.py":
        "fb31d085498162ca9681d7a0b9bb727c84359916f18b9069eb1ce8cf89160b0f",
    "tests/test_s168_light_lanes_24.py":
        "7c726ba52f390c51a519556a8ffdc623d3b3698cfc403157c8ec7befe19a45b4",
    "tests/test_s169_light_lanes_25.py":
        "289486657fbdc838d506fbae2a84808a5f6a28d10d2462b7cb0baa343fe5d4d9",
    "tests/test_s170_light_lanes_26.py":
        "ce4361e15e35f9dfaeadb9aadd01590ca0604fb0955dca5e288d97e71e21bbd3",
    "tests/test_s171_light_lanes_27.py":
        "7bbfd7fbeeccce80b02985d1fd3222beaac901c1ab87d16f6f1ee1e0a2f2d177",
    "tests/test_s172_light_lanes_28.py":
        "fa0440459e10353c9c30fa54260c4c1c8aaebfb5771614f3e66d078dac0fb069",
    "tests/test_s173_light_lanes_29.py":
        "7116cde889e7e704cebd77bdcbac43fe2a23b0d28e07f5e80389d7181218386a",
    "tests/test_s174_light_lanes_30.py":
        "9e0d152b95ed3e6fe0e715bc7401290cf9632015ebe23418185d3417f6acc767",
    "tests/test_s175_light_lanes_31.py":
        "72e4f1dd8facea5e9d8c758b4336f7116de834deed1f31c6b25d484a4fb7fbe2",
    "tests/test_s176_light_lanes_32.py":
        "6cd4c5de415ccdbd7114d96a4fc0c53be37616d50c5d1d434d9e03516aa4e41f",
    "tests/test_s177_light_lanes_33.py":
        "544cf6b518603fff8a2669a296ed68ed9e9f6cd305bb57fc325f050b652eaaca",
    "tests/test_s178_light_lanes_34.py":
        "edd242b5e4a7717a0583e7299f57fffc70b3f913b44381161db7279df4585bb1",
    "tests/test_s179_light_lanes_35.py":
        "272c6c9c4893c8bd420dd23e5ec52a4de1eec4420d47b81eab87b13b186593c6",
    "tests/test_s180_light_lanes_36.py":
        "4c60e1e17db465225c68f5487f083bbdb11845ea96dd4820753207f4305c11ed",
    "tests/test_s181_light_lanes_37.py":
        "acf23f7e6cab3d3e1ffd807db6dd43eaf0857bf4364bc1f5d6e4cd94e82656d3",
    "tests/test_s182_light_lanes_38.py":
        "aa4985288594eefa9ce0e07635b96b23340045e59e2a0a88afb432da6a8b533d",
    "tests/test_s183_light_lanes_39.py":
        "d78ba8e9319c5b03e58eb5161accb253f9694eabfa2999f59d992a88acc95bbf",
    "tests/test_s184_light_lanes_40.py":
        "6e4b43cbc6e01b4e204c866081a200a39421f1c29145bc17ecac222e2caa945f",
    "tests/test_s185_light_lanes_41.py":
        "fc28f922833faffa21002f35afc588a81be839e84b9ad18d5934c4350b06ff0f",
    "tests/test_s186_light_lanes_42.py":
        "1a63705ec3480dc9164ce0da1e4e13d8577a2f4468bf57e61ca0075e9c28373c",
    "tests/test_s187_light_lanes_43.py":
        "08d1c50c95508a256bf0189924f704f99267b8a557f4968a311e65a209c5e0a6",
    "tests/test_s188_light_lanes_44.py":
        "06e071de2e2c7f4fad6c409f3d8d61a662e23b4c1c9b83c247eb7ace5c84a132",
    "tests/test_s189_light_lanes_45.py":
        "760a184eb8ba2c2b063fee1b41b2b6f8dd0a1911ec4d02560e751f9e8f9ac18e",
    "tests/test_s190_light_lanes_46.py":
        "00f975aadbef1a6f051ed3d03f02eef6f244d69f44caefda68b954b392e0c48b",
    "tests/test_s191_light_lanes_47.py":
        "5e481d7e048570cb1d8d1befbf8e13d03dd38242644371f6a8c9f2bddf0e4188",
    "tests/test_s192_light_lanes_48.py":
        "7d8a52a12777501070afb9548184c93e83807c2c15cbaa2f20d7e2fd1aee6064",
    "tests/test_s193_light_lanes_49.py":
        "ca343ca71368327b75e4622b7dae63ee0b2ed84e246d9bba3a5197461990e867",
    "tests/test_s194_light_lanes_50.py":
        "b2e0ebdf85bd7875300d3515907fb42dc28a67e4ef5caf84a597aba3f894e6f2",
    "tests/test_s195_light_lanes_51.py":
        "c19e10af2f5d11d9ee875b94cf3d2316c2509d30a5a1d1c7e6acc692c26284c7",
    "tests/test_s196_light_lanes_52.py":
        "06c1dd42e2a28d3a4e20b2879c795d9c4e1c951ab22bb93392f9249e42a2809b",
    "tests/test_s197_light_lanes_53.py":
        "4ad31fc384b256e4b7dd3de641ca852928c5743a01c1a200dff03f9cb5ebfc91",
    "tests/test_s198_light_lanes_54.py":
        "8bc0e65c652b14e04b22df0364c80f225fe36bae42e151d953ea934ef4071a80",
    "tests/test_s199_light_lanes_55.py":
        "f8b5d1090ef92d01f26a19340ea5d9a895060088c968359c83d878cd35fe0b52",
    "tests/test_s200_light_lanes_56.py":
        "9531084d870cad82e1618382171746427c82776082a4f7ebe7d0be90591be7cb",
    "tests/test_s201_light_lanes_57.py":
        "3aae00c7ca876683dc6d80c9b6a0b6b4d6f3e49646991e1fc1de191aeb2f8337",
    "tests/test_s202_light_lanes_58.py":
        "0cc084b3e6556e84fa186ed4d02632f7f5e7172d6d5def3059e222494b296ad2",
    "tests/test_s203_light_lanes_59.py":
        "17b808cd7f09c4001ecda5f35844eba92902198980f7c7f4ceb61e26cb5d28d9",
    "tests/test_s204_light_lanes_60.py":
        "8de6623754db0d184f962987a0bfc44691fac3d7ded4000d3a2d28322e3098e7",
    "tests/test_s205_light_lanes_61.py":
        "f252960eaacf23feae472893db3122040fc46495681db26471db12d580ada138",
    "tests/test_s206_light_lanes_62.py":
        "94cc74a16b4a896231040e9b141edd1b4347b9ae790b7536b97ce1d8d6717957",
    "tests/test_s207_light_lanes_63.py":
        "4d7ea1a48f6df913fe88ff3d93a8656188fabb529ac54d89953cec3327750251",
    "tests/test_s208_light_lanes_64.py":
        "22e323740e27877f3b31d8af6a6e41d4ca2205e352be6ea37491aded9e7b127f",
    "tests/test_s209_light_lanes_65.py":
        "f85f0a57b1031d739fd600d60a9bb2bdece627e7dc42a3c17964b84b7e6a95ae",
    "tests/test_s210_light_lanes_66.py":
        "85fd7cc456dc38312faa2bd76078d554acff58ce63cc68cbc16543885047e401",
    "tests/test_s211_light_lanes_67.py":
        "960b130d90ed65912f27af76eb9a91b973cc80132f444457abd21560df885a70",
    "tests/test_s212_light_lanes_68.py":
        "904c2b402a5e05cce542e95e09cb9141cec9b33ce9ea9d32085b95141722a640",
    "tests/test_s213_light_lanes_69.py":
        "efb7b572e207da1656b30ea6da8a46980ddfa2569dae9175880e75a86d16bd53",
    "tests/test_s214_light_lanes_70.py":
        "225d9d21776c4d0ff4fabad1d5430d2ee4254ee3ca8c3ff21219cf5c345ebece",
    "tests/test_s216_light_lanes_71.py":
        "38f5b3a1b0ec29d89706693fe67943db40e99af458d2f79eb9b24aca23f36f92",
    "tests/test_s217_light_lanes_72.py":
        "85d4644a40f13765709aa72adcb0eff852fbe0c58e3faef9591e8d8f5c3df070",
    "tests/test_s218_light_lanes_73.py":
        "a0cdfda52fae35563c88f3b6cb37f3ff5fc219339c998e6a0dedb1913191727d",
    "tests/test_s219_light_lanes_74.py":
        "b44929ecb8e74e44ce333eb63aad62e807495d47ef0d4e3297da66b437fa41df",
    "tests/test_s220_light_lanes_75.py":
        "a18431a63920c75ddf1f9658aeb3f5fdeffffae8204316964852ace7297f85b0",
    "tests/test_s221_light_lanes_76.py":
        "1822fe5f9c5990320750085fdbcc3577b4eee8badaa0b496217d0c047ec2af6a",
    "tests/test_s222_light_lanes_77.py":
        "32435e82ae7c782edaed2e639a92d39d22289c3659092c107055961c9d816b54",
    "tests/test_s223_light_lanes_78.py":
        "ea8b61b07439e19ae2944b40b2dbf43a5c3e0624a3eeb27868a4b563aea5c6e9",
}

# The bounded probe result (one call, 2026-09-22).
PROBE = {
    "route": "glm",
    "model": "glm-5.3",
    "rc": 0,
    "reply": "ok",
}

S136 = Path(__file__).resolve().parent / "test_s136_route_probes.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_guard_versions_still_current() -> None:
    """Each recorded guard hash still matches the file's bytes."""
    repo = Path(__file__).resolve().parents[1]
    moved = [
        rel
        for rel, recorded in GUARD_VERSIONS.items()
        if _sha256(repo / rel) != recorded
    ]
    assert not moved, f"guards moved since the {SWEEP_DATE} sweep: {moved}"


def test_serve_table_still_claims_serving() -> None:
    """The s136 serve table's glm verdict still claims serving glm-5.3."""
    spec = importlib.util.spec_from_file_location("_s224_s136", S136)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verdict = module._SERVE_TABLE[PROBE["route"]]
    assert verdict.startswith("serving"), f"the glm verdict drifted: {verdict!r}"
    assert PROBE["model"] in verdict, f"the verdict lost the model: {verdict!r}"
