# TRANQATHMA Register of the Seventeen Goals

A public register of the seventeen Sustainable Development Goals: India's official
figure, the world figure beside it, and the distance to the best value any country
has attained. Every number names the document it came from and the day it was read.
Where no admissible source exists, the space is left blank.

    tranqathma.github.io
    Build it for Society

## How it runs

Four times a day, GitHub starts a machine, runs the seventeen goal agents, and
shuts down. Each agent opens its two assigned sources, one Indian and one
international, stores each document with a fingerprint, and stops if nothing
changed. If something changed it reads out the new value, has it independently
rechecked, and writes it into `data/`. The Master Agent then weighs all seventeen
and proposes what deserves the front page. The site rebuilds itself and publishes.

Mechanical changes publish themselves. Editorial judgment waits in the War Room
for a named human.

## Layout

    agents/core.py          the machinery every goal agent shares
    agents/run_all.py       one run of the whole workforce
    agents/master.py        the Master Agent and its weighing table
    agents/make_charters.py writes the charters from the assignment table
    charters/               eighteen charters, one per agent
    data/goals.json         the seventeen goals, owned by the agents
    data/site.json          headline figures and the War Room queue
    snapshots/              every source document as received, never edited
    build/generate.py       the site builder
    build/theme.css         the design
    index.html goals/       the published site, rebuilt every run
    .github/workflows/      the four times daily schedule

## Run it yourself

    python3 agents/run_all.py --build     one full run, then rebuild the site
    python3 build/generate.py             rebuild the site from existing data
    python3 agents/make_charters.py       regenerate the charters

## Publishing on GitHub Pages

Settings, Pages, Deploy from a branch, main, folder `/ (root)`.

## The rules this register holds itself to

1. The indicator is named before the value is sought, and never swapped because
   the number it produces is unflattering.
2. The comparator is the best attained value, never a target.
3. Where two admissible sources disagree, both are published and neither is
   averaged away.
4. Where no admissible source exists, the space is left blank.
5. A correction is a new dated revision, never a silent edit.
