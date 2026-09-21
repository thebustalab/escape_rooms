#!/usr/bin/env python3
"""test_waterfalls.py — pins each graded room's answer to data/reliquary_phials.csv (recomputed in base R, the
students' tool) and asserts decoder-key lockstep. Run: python3 test_waterfalls.py"""
import json, os, re, subprocess, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
R = r'''
d <- read.csv("%s"); v4 <- c("clarity","mineral","resin","ash"); v5 <- c(v4, "weight"); set.seed(7)
km <- kmeans(d[, v4], 3, nstart = 25); cat("largest", max(table(km$cluster)), "\n")
wss <- sapply(1:6, function(k) kmeans(d[, v4], k, nstart = 25)$tot.withinss)
drop <- -diff(wss); cat("elbow", which.max(drop[-length(drop)] / drop[-1]) + 1, "\n")
m <- tapply(d$resin, km$cluster, mean); cat("resin_n", sum(km$cluster == as.integer(names(which.max(m)))), "\n")
ks <- kmeans(scale(d[, v5]), 3, nstart = 25); j <- which(d$phial == "Jasper")
cat("scaled", paste(d$phial[ks$cluster == ks$cluster[j]], collapse = ","), "\n")
ku <- kmeans(d[, v5], 3, nstart = 25); cat("unscaled", paste(d$phial[ku$cluster == ku$cluster[j]], collapse = ","), "\n")
''' % os.path.join(HERE, "data", "reliquary_phials.csv")


class Waterfalls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = subprocess.run(["Rscript", "-e", R], capture_output=True, text=True, check=True).stdout
        cls.r = {l.split()[0]: l.split()[1] for l in out.strip().splitlines()}
        doc = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
        cls.hs = {r["key"]: {h["id"]: h for h in r.get("hotspots", [])} for r in doc["rooms"]}

    def test_station1_largest_family(self):
        q = self.hs["station1"]["font"]["question"]
        self.assertEqual(q["options"][q["correct"]], "%s phials" % self.r["largest"])

    def test_station2_elbow(self):
        self.assertEqual(self.hs["station2"]["font"]["pick"]["answer"], self.r["elbow"])

    def test_station3_resin_family(self):
        self.assertIn("== %s)" % self.r["resin_n"], self.hs["station3"]["font"]["check"]["expr"])

    def test_boss_scaling_trap(self):
        q = self.hs["boss"]["master_font"]["question"]
        scaled, unscaled = self.r["scaled"].split(","), self.r["unscaled"].split(",")
        ans = q["options"][q["correct"]]
        self.assertEqual(ans, "Selenite"); self.assertIn(ans, scaled)
        # exactly one option is right when scaled, and the decoy is the unscaled weight-band mate
        self.assertEqual([o for o in q["options"] if o in scaled], [ans])
        self.assertIn("Antimony", q["options"]); self.assertIn("Antimony", unscaled)

    def test_decoder_lockstep(self):
        src = open(os.path.join(HERE, "..", "..", "..", "decoder", "decode_codes.R")).read()
        vec = re.search(r"FLAT_CLUSTERING_WATERFALLS_KEY <- list\(\s*scenario_id = 10,\s*correct = c\(([^)]*)\)", src)
        self.assertEqual([int(x) for x in vec.group(1).split(",")],
                         [self.hs["station1"]["font"]["question"]["correct"], 1, 1,
                          self.hs["boss"]["master_font"]["question"]["correct"]])


if __name__ == "__main__":
    unittest.main()
