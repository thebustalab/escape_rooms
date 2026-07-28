/*
 * scenario.js — "Field Analyst: Data Visualization" (chapter 1 chain, TRIAL).
 *
 * JOURNEY / chain mode (flow: "journey"): rooms are worked in order. Each room
 * is one narrative case with its own scene; solving its multiple-choice unlocks
 * the door onward. The final room is the boss — the figure deliverable.
 *
 * Content is drawn from teaching/CHEM5725/exercises.csv (the Data Visualization
 * set: Alaska lakes + Hawai‘i aquifers). Answer indices are 0-based; the sheet's
 * `correct_answer` is 1-based, so subtract 1. Framing device: an analyst working
 * a stack of field case-files, stepping into each one.
 */
window.SCENARIO = {
  id: 3,
  slug: "datavis1",
  title: "Field Analyst — Data Visualization",
  flow: "journey",

  packages: ["readr", "dplyr", "ggplot2"],
  datasets: [
    { name: "alaska_lake_data",
      url: "https://thebustalab.github.io/phylochemistry/sample_data/alaska_lake_data.csv" },
    { name: "hawaii_aquifers",
      url: "https://thebustalab.github.io/phylochemistry/sample_data/hawaii_aquifers.csv" },
  ],
  setup: "suppressMessages({library(readr); library(dplyr); library(ggplot2)})",

  screen1: {
    image: "scene/alaska_station.png",
    title: "The case-file desk — 23:40",
    story: `
      <p>Two field cases have landed on the analyst's desk tonight, each from a
      different corner of the map, each waiting on the same tool: a good plot.</p>
      <p>Work them in order. Crack the first, and the next file opens. Clear both,
      and the night's real job remains — the figure that goes to the field team.</p>
      <p class="byline">Enter your x500 to sign the case log, then open the first file.</p>
    `,
    enterLabel: "Open the first case-file →",
  },

  briefing: `
    <p>Two datasets are loaded: <code>alaska_lake_data</code> and
    <code>hawaii_aquifers</code>. Explore on the left; each case tells you which
    one you need. Answer the case question to unlock the door to the next room.</p>
  `,

  nodes: [
    {
      key: "alaska",
      type: "spoke",
      technique: "data visualisation",
      title: "The warm lake (Noatak)",
      scene: "scene/alaska_station.png",
      intro: `A bush plane is down in the Noatak Preserve, yet the beacon still
        transmits hours past the cold-water survival window. If one glacial lake
        runs warmer than the rest, that is where the team should search first.
        Plot the Noatak lakes by water temperature and find the outlier.`,
      starterCode:
        'library(dplyr)\nlibrary(ggplot2)\n\nalaska_lake_data %>%\n  filter(park == "NOAT") %>%\n  ggplot() +\n  geom_point(aes(x = water_temp, y = lake))',
      prompt:
        "Filter to Noatak (<code>park == \"NOAT\"</code>) and compare water temperature across lakes. Which lake should the team search first?",
      options: [
        "Devil_Mountain_Lake", "Imuruk_Lake", "Kuzitrin_Lake", "Lava_Lake",
        "North_Killeak_Lake", "White_Fish_Lake", "Iniakuk_Lake", "Kurupa_Lake",
        "Lake_Matcharak", "Lake_Selby", "Nutavukti_Lake", "Summit_Lake",
        "Takahula_Lake", "Walker_Lake", "Wild_Lake", "Desperation_Lake",
        "Feniak_Lake", "Lake_Kangilipak", "Lake_Narvakrak", "Okoklik_Lake",
      ],
      correct: 18, // Lake_Narvakrak (sheet: 19, 1-based)
      maxAttempts: 4,
      feedback: {
        correct: "That's it — <strong>Lake Narvakrak</strong> sits far above every other Noatak lake. The door to the next file clicks open.",
        wrong: [
          "Filter to <code>park == \"NOAT\"</code> first, then look for the point far to the right.",
          "Map temperature to x and lake to y so the outlier stands out.",
          "One Noatak lake is near 18&nbsp;°C while the others sit below 7&nbsp;°C.",
        ],
        reveal: "The warm outlier was <strong>Lake Narvakrak</strong>. Recording your last answer.",
      },
    },
    {
      key: "hawaii",
      type: "spoke",
      technique: "data visualisation",
      title: "Saltwater intrusion (Hawai‘i)",
      scene: "scene/hawaii_station.png",
      intro: `A statewide aquifer survey needs a warning sent to the communities
        whose wells show elevated sodium and chloride — the signature of saltwater
        intrusion. Plot sodium and chloride across the wells, find the ones that
        stand out, and read off which region they belong to.`,
      starterCode:
        'library(dplyr)\nlibrary(ggplot2)\n\nhawaii_aquifers %>%\n  filter(analyte %in% c("Na", "Cl")) %>%\n  ggplot() +\n  geom_point(aes(x = abundance, y = aquifer_code)) +\n  facet_grid(analyte ~ .)',
      prompt:
        "Find the wells with elevated sodium and chloride. Which community needs to be contacted about saltwater intrusion?",
      options: [
        "North Kohala", "Kohala Coast", "Kona", "Kau", "Puna", "Hilo", "Hamakua",
        "Windward O‘ahu", "Leeward O‘ahu", "North Shore O‘ahu", "Central Maui",
        "West Maui", "East Maui", "South Shore Kaua‘i", "Lana‘i", "Moloka‘i",
      ],
      correct: 2, // sheet: 3 (1-based) — adjust here if the key differs
      maxAttempts: 4,
      feedback: {
        correct: "Warning sent. With both cases cracked, the night's real task is all that's left.",
        wrong: [
          "Filter to <code>analyte %in% c(\"Na\", \"Cl\")</code> and look for the high-abundance wells.",
          "Colour or label by <code>well_name</code> to see which wells the outliers are, then place them by region.",
        ],
        reveal: "Recording your last answer and moving on.",
      },
    },
    {
      key: "boss",
      type: "boss",
      technique: "the field-brief figure",
      title: "The brief figure",
      scene: "scene/alaska_station.png",
      brief:
        "Both cases are closed. Now make the single figure the field team will act on: pick whichever case you found most urgent and build the plot that makes its answer unmistakable at a glance.",
      figureSpec:
        "one clear plot — the right data, the outlier or signal obvious, readable in two seconds by someone who wasn't in the room.",
    },
  ],

  finishMessage: `
    <p>Both files cleared and the brief figure is ready. Copy your case code below
    and submit it to Canvas together with your figure.</p>
  `,
};
