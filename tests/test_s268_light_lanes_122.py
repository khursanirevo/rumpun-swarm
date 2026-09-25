"""s268 w1: the light lanes record.

Ground truth measured 2026-09-24 (solo):

- the guards re-ran fresh solo over this record's 123-file
  pin basis (the s267 record's 122 pins plus the s267
  record itself): 248 collected, 248 passed in 3.19s, rc 0,
  /tmp/s268-w1-guards.log. The pin list was script-generated
  from the s267 record's GUARD_VERSIONS plus the s267 record
  itself, so the pinned set is exactly the run's files. Every
  guard is green fresh, and the guard files did not move
  (all 122 s267-recorded hashes still match the bytes; the
  s267 record itself landed fresh).
- drift: none named. All 122 s267-pinned guard files match
  the recorded versions, the readme-verbs guards included.
  No new drift. No naming drift to name: the brief carries
  the next-free per-family convention natively (the s258
  proposal merged in a40bc98). This record takes the next
  free name (tests/test_s268_light_lanes_122.py).
- one bounded route probe re-confirmed the serve table: the
  pinned glm route call (.rumpun/rumpun.yaml line 38),
  --model glm-5.3 (the s125 through s267 season precedent),
  one call, rc 0, stdout reply ok (3 bytes, the s265
  through s267 runs recorded the same). The stderr carried
  the known catalog warning (CLI-side text, the s125
  classification, 788 bytes, byte-identical to the
  s267 stderr, cmp rc 0). Trail: /tmp/s268-w1-probe.out and
  .err (prompt: /tmp/s268-w1-probe-prompt.txt, rc:
  /tmp/s268-w1-probe.rc).

The record: the guards' versions (sha256 of each guard file's
bytes), the probe result, the sweep date. Reads only: no
network, no writes.

A red on the versions pin means a guard moved since this
sweep. The next steady-state cycle (s269) re-runs the guards,
refreshes the record, and adds this file to the pins.
"""


from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

SWEEP_DATE = "2026-09-24"

GUARD_VERSIONS = {
    "tests/test_s128_readme_verbs_lint.py":
        "5795fa17b6831697116554833514f41547b42d3642ef1da183c28051b2bc1378",
    "tests/test_s136_full_guide_lint.py":
        "208e9054eedc61cc7d590d99caf5fbc50821ccc81d8d793e81d7fbd36a77642e",
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
    "tests/test_s224_light_lanes_79.py":
        "8c732449348deaaf139e1428b09e7aa1a316e8c01797b0e783c921189481f4eb",
    "tests/test_s225_light_lanes_80.py":
        "754e035a8117a44623aa763d2f0045ec4550ab8d7b71625fc236e3b6c5df9dd7",
    "tests/test_s226_light_lanes_81.py":
        "59e8eea13f0d8a628fafa6ffff2f313df099ea7265d4690e75080e8f90ba5a30",
    "tests/test_s227_light_lanes_82.py":
        "3e4e5bf34adae01adb70e40934c8b174edda72732c92208655478d86fb3b0cf7",
    "tests/test_s228_light_lanes_83.py":
        "21365fa14fa9af50a1018139577956097daea18d6f427a8142da05719a38e569",
    "tests/test_s229_light_lanes_84.py":
        "a48e8e9171da969311dd2b70c538e132d954dd96b1ea676cf5bf5fe2b42f3f03",
    "tests/test_s230_light_lanes_85.py":
        "b6b3e9ff1f592f596516be89265be3c50c81cf3f47de4f353106d4c7e7655530",
    "tests/test_s231_light_lanes_86.py":
        "d674da4c06c9876264f25756072a6ffc93f76bcb15efa81eaea37acae783d36f",
    "tests/test_s232_light_lanes_87.py":
        "9c75c8f30e849e490a828c95f76183428990dee336359640f5790b03f34dccba",
    "tests/test_s233_light_lanes_88.py":
        "b237ccc102aa62100a679e97493bab9d073aec4ba0d2854c9b2769b6f2dae9e4",
    "tests/test_s234_light_lanes_89.py":
        "4dc189824b3323125c7600c9c4b1fc26bfec9908061d38c6e61a223c5894422e",
    "tests/test_s235_light_lanes_90.py":
        "497feb394d6d9d9b8761938cdd7e99bd8c366e54f27ba3dd456d2abba53d3aa3",
    "tests/test_s236_light_lanes_91.py":
        "f7c2f7168773a78481b0624dce6cadddfe8784088e9241887d0a737586b16b96",
    "tests/test_s237_light_lanes_92.py":
        "b41b1f8fee3b9b955624f8f777bab2a79b3d102c4df577bf33128cc04d343486",
    "tests/test_s238_light_lanes_93.py":
        "baa4e5b04c714dfe46cb484e71e4f540007c3ac603952cac8e0f65704fbccb76",
    "tests/test_s239_light_lanes_94.py":
        "8f1773f99a09887f384d44e396eda5d8d92318108e022a85d59db47a5b0fb2d6",
    "tests/test_s240_light_lanes_95.py":
        "6c8765aefdb63f44fb8b814d42c5ee52ec55979cc1b07d77db82940959060d2b",
    "tests/test_s241_light_lanes_96.py":
        "f800aa9b6c6c3a402c914b826f041a5120efaa9288fe5db763af400663e120a0",
    "tests/test_s242_light_lanes_97.py":
        "a4c5b87d488ac076c83eec0471abc364f7c2e3477f222b600a18d51fd5e2588b",
    "tests/test_s243_light_lanes_98.py":
        "8baa16a8fc64743974a45c037afb98ef2cbf8e1a5cfd3b85c393c463a4606521",
    "tests/test_s244_light_lanes_99.py":
        "0e71cbc3fbba237bb26eb3e64112ec3b2b9c437dabac3894d6444ef7a0857076",
    "tests/test_s245_light_lanes_100.py":
        "2d5d0de16afe3221e94bbdec5a5d8f5202e44d68b6ae799c8f9f9b71d74ea26f",
    "tests/test_s246_light_lanes_101.py":
        "40fc2d376d81ec1282238ccd90b3fc8a5186631473454048817b40912f22ee58",
    "tests/test_s247_light_lanes_102.py":
        "5004e241a63b13b4e9ac3b212cd43023071e00338cfcf3c144b78c94a30f904a",
    "tests/test_s248_light_lanes_103.py":
        "b9b2e55f627fff1e90962f7adae0054d74695778253fc3c6038de5ffdbed4447",
    "tests/test_s249_light_lanes_104.py":
        "5c84dede776e07bfafe960405c1bcbcba1673c399ab7a0a5f0bff8b2ba0f6231",
    "tests/test_s250_light_lanes_105.py":
        "c000729943d7ffec74bf61587a72ccef03fe53e88e57ffe5e295fe79a7cb65d3",
    "tests/test_s251_light_lanes_106.py":
        "8e42851749c7d9d15937cd32764e61c64fdaaf0912023f28dd8d14edae61d497",
    "tests/test_s252_light_lanes_107.py":
        "433227e33ba365b9191b4e885c6391ecafe4f9cd2f263e68b83cb1562982c9a6",
    "tests/test_s253_light_lanes_108.py":
        "4016097a8ec81257f508425ba94221ba3fafc094f434d9de95ba8d76d0ad38c4",
    "tests/test_s254_light_lanes_109.py":
        "d8d4593efd6e958011b3eaad4165d5e863313838d21b2c2842f60ba8f5c0cc1e",
    "tests/test_s255_light_lanes_110.py":
        "0904f0073aa15bd0cf1a1368215c08bdce44f4a6a4d2b0943e098393087ed8b1",
    "tests/test_s256_light_lanes_111.py":
        "687d8d0cc5abc4773183bb8ae139a8d33b8297d7d290e05579260df1fee6b546",
    "tests/test_s257_light_lanes_112.py":
        "e6410790a2ebaf54603971baeed3d13de00106b18ee2cdccf246a036ef8f718d",
    "tests/test_s259_light_lanes_113.py":
        "06d518d90f90a2a726710818c6596b686b3e9572c1a4ef20548afa23b6ab0769",
    "tests/test_s260_light_lanes_114.py":
        "acfe508e011407315f05df32ffe9bdb4c6d8d16309641d11e57c7dd81f889a3f",
    "tests/test_s261_light_lanes_115.py":
        "bfb80c28fd7d778fbac626711b213833eb8f679426308162c3c7a87f206c8ae5",
    "tests/test_s262_light_lanes_116.py":
        "f087120d8bd53166f5659a9cac7cef00327c6c13de111622e7c76c40b15ef814",
    "tests/test_s263_light_lanes_117.py":
        "269697fb7e0d61318b822e9d2fe4d115364f6305a2f97e257a650a902a592d2a",
    "tests/test_s264_light_lanes_118.py":
        "1446c7a31bac6600b3fae7dc436d05abf0583b2566594e4bb2f6e96641dca1ba",
    "tests/test_s265_light_lanes_119.py":
        "955c5972ad75dfb4e5b57bd8ee3cb3501d560e45477f8b8069cb34e0e0c478dd",
    "tests/test_s266_light_lanes_120.py":
        "5393322350152a5d17391a89e8d1c86a9bd95e24c4117eada720d955143c1eee",
    "tests/test_s267_light_lanes_121.py":
        "975f11cb36eba7175bb1059e62ec18ebfdeff84d080fd33e868829a078589d93"
}

# The bounded probe result (one call, 2026-09-24).
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
    spec = importlib.util.spec_from_file_location("_s268_s136", S136)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verdict = module._SERVE_TABLE[PROBE["route"]]
    assert verdict.startswith("serving"), f"the glm verdict drifted: {verdict!r}"
    assert PROBE["model"] in verdict, f"the verdict lost the model: {verdict!r}"
