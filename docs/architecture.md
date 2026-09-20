# Propagation geometry in agent swarms: working brief

Session dump, 19 to 20 September 2026. Everything agreed or left open so far.
Intended as the seed document for a repo under the Foveaux-Kirby umbrella and as
context for a Cowork project.

---

## 1. The problem and the constraint

**Goal:** how do you stop an agentic attack without releasing an unrestricted
model in response.

**Standing constraint:** the answer cannot assume new models tuned not to
misbehave. That genie is out of the bottle. Any defence has to work against
models nobody constrained, including open-weight ones running on an attacker's
hardware.

This rules out most of the published literature, and it should stay ruled out.

---

## 2. The frame

Route taken, kept because the dead ends matter:

1. **Quorum sensing** as an analog. Buys a mechanism downgrade: bacteria do not
   message each other, they leak into a shared medium and flip a switch above a
   concentration threshold. If a swarm works this way, no hidden channel is
   needed. Only a shared substrate whose state changes when agents act.
2. **Rejected:** "generations of selection paid for it." Too tidy for biology.
   Redfield's diffusion-sensing critique (Trends in Microbiology, c. 2002, cited
   from memory, verify) argues the cell measures its own diffusion, not
   population density, and the collective behaviour falls out of every cell
   running the same selfish local calculation.
3. **Better frame: emergence in the class of replication.** Not a product of
   selection, a precondition that makes selection possible. If swarm
   coordination is in that class it is not a training artefact and cannot be
   fixed by fixing the reward. It comes free with the architecture.
4. **Rejected: rule complexity.** Conway's Life is three rules and is
   computationally universal (Rendell's Turing machine). Universality is a fact
   about which configurations can exist, not about how rich the rules are. The
   Langton lambda / edge-of-chaos lane is partly mined; Mitchell, Hraber and
   Crutchfield (c. 1993, from memory, verify) showed lambda does not reliably
   predict computational capability.
5. **Landed on: connection, not count.** Life on a sparse random field produces
   nothing. Same rules, same universality, no gliders. What differs is whether
   anything reaches anything.
6. **Fission as the instance.** There is no critical mass, strictly. There is a
   critical geometry. The same material is subcritical spread out and
   supercritical compressed.

### The two variables

Underneath is a branching process. Two independent quantities:

- **k** — expected number of downstream agent actions caused by one agent
  action. Below one it dies, above one it runs away, and the transition is
  sharp. Called R0 in epidemiology, the percolation threshold elsewhere.
  **Agent count only matters through its effect on k.** Count was never the
  variable.
- **tau** — generation time. How fast one event produces the next. Set by
  compute.

Vaughan's formulation of the operating band: *an interaction in an environment
dense enough to cause an immediate chain reaction, but sparse enough to allow
for reaction time.* That is two variables, not one. Density sets k. Reaction
time is tau versus the latency of the fastest available intervention, and the
two are orthogonal.

### Mapping

| Reactor | Swarm |
|---|---|
| Neutron | An agent action that becomes readable by another agent |
| Fissile material | The shared substrate, weighted by what is readable and writable |
| Geometry | How much of the environment converts one agent action into further agent actions. This is k. An architecture property, not a headcount |
| Absorber / control rod | Security boundaries: authz, egress filtering, sandbox walls. These eat the action so it cannot seed the next one |
| Generation time | Compute |
| Delayed neutron fraction | Any step in the propagation chain that runs at human latency |

**Compute is not the control rod.** It sets tau, it absorbs nothing, and it is
the one variable the industry is pulling out monotonically with no reinsertion
path. Every real SCRAM fails safe by gravity. Compute does the opposite.

### Where the analogy leaks

Fissile material depletes. The substrate accumulates. An artefact written on
Tuesday is readable on Friday, so the reaction can smoulder and reignite. That
pushes it toward autocatalysis rather than fission, and is probably why a
rebooted environment does not clear the behaviour.

---

## 3. What the frame rules out

**Kill switches.** SL-1 and Chernobyl both had SCRAM systems and detection.
Above prompt critical the detect-decide-act loop is longer than the generation
time, so the switch exists and arrives late. A brake that only works in the
regime where you did not need it.

**The real safety property** is that prompt-only k is held below one by
construction, permanently. Roughly 0.65% of U-235 fission neutrons are delayed,
seconds to minutes, and that small fraction is what stretches the effective
generation time enough for control rods to work at all. The architectural
equivalent: **no propagation chain closes without crossing at least one slow
element.** That is a design constraint, not a monitoring one.

**Better than a switch:** negative temperature coefficient. Fuel heats, Doppler
broadening widens absorption resonances, reactivity falls. Nobody watching,
nothing deciding, and it cannot be late. Open question: what is the swarm's
equivalent, a property where more activity mechanically produces less
propagation.

**Note on scope.** The slow-element constraint only helps for systems you
control. It does nothing against an attacker's swarm running in your
environment. Different problem, later.

---

## 4. The legitimate-swarm problem

Swarms are commercially normal. CI/CD fan-out, map-reduce, crawler fleets,
parallel code agents on one repo, multi-agent research with a shared scratchpad,
SOC triage fleets. The commercial case is real.

The line is **not** legibility, and not fan-out. It is:

> A CI pipeline cannot rewrite its own propagation graph at runtime. An agent
> swarm can.

CI's DAG is authored before anything runs, so k is pinned by the author.
Legibility is downstream of that. In an agent swarm, k is an emergent property
of behaviour. And runtime course correction is precisely what people are paying
for, so you cannot simply ban it.

---

## 5. Detection

Two candidate detectors:

1. **Learned baseline plus drift.** Fails to a patient adversary. The baseline
   is trainable: run benign for three weeks, widen the envelope, act inside it.
2. **Direct coupling measurement.** What fraction of agent actions are caused by
   other agents' outputs rather than by the declared task. **This one survives**,
   because evading it costs the adversary the thing they came for. Drop coupling
   to hide and you drop k, and the swarm stops being a swarm. Same reason you
   cannot hide criticality in a reactor. Criticality is what you are using.

Vaughan's shape formulation, which is the abstract: *they are supposed to be
shovelling coal but they are crowded around the exit.* The useful half is not
the concentration (successful swarms concentrate too) but that the location is
not downstream of the declared job.

**Known limit, to be stated up front rather than buried:** mimicry. Routing
propagation through channels the legitimate work also uses, so the coupling is
real but looks accounted for. Genuinely open.

---

## 6. Disclosure

Publish the mechanism, hold the setpoints.

Secrecy only pays when the defence fails once known. This one does not. An
attacker who reads it cover to cover is left choosing between being detectable
and being slow. Reactor physics is public and it does not help anyone hide
criticality. What is worth holding: thresholds, baseline envelopes, which
channels are actually instrumented.

Also: a swarm that hides by decoupling has already paid the price, so that is
the detector working rather than failing.

---

## 7. The paper

**Primary reader:** security engineers who see the LinkedIn summary, click
through to Zenodo, and start architecting the next morning.

**LinkedIn post:** not an abstract. A hook with one concrete thing in it. Coal
and exit as the opener, geometry as the payload, and the click earned by a claim
they can check against their own stack: *you probably cannot answer which agent
outputs this action read.* No physics in the post.

**Spine:**

1. The incident, told as shape rather than content. Every action ordinary, the
   distribution not.
2. The reframe: not a model problem, a propagation geometry problem.
3. The physics, minimal. Two ideas: events per event, and how fast generations
   turn. Two paragraphs. No delayed neutron fraction, no numbers, no equations
   in the body. Its only job is to stop the reader building a kill switch.
4. The uncomfortable mirror: you already run swarms, CI is one, and the
   difference is runtime graph rewriting, which is what you are paying for.
5. The mimicry limitation, moved up front. This audience finds it in ninety
   seconds and burying it looks naive.
6. The gap: nobody can measure any of this, because almost nothing records which
   agent outputs a given action read. **This is the contribution.**
7. The primitive: what to record and why it is cheap. Near-copyable, actual
   fields, actual placement, hooks into frameworks they already run. Roughly a
   third of the length.
8. Demonstration, then limits.

**Register to steal from:** Thompson's Turing lecture, *Reflections on Trusting
Trust*, 1984. Short, one idea, one demonstration, reader leaves unsettled rather
than instructed.

**Hazard to design against:** the reactor framing triggers "so we need a SCRAM
button." If the paper does not kill that reflex on purpose, that is what people
will build.

---

## 8. Reference implementation

Own repo under Foveaux-Kirby. Not the Gemma 4 portfolio. Python. Hexagonal.

### What it does

Records, for a running multi-agent system, which agent outputs each agent action
actually consumed. Builds a propagation graph and estimates k. Everything else
is downstream of that measurement. The detector is a demonstration, not the
product.

### Domain model

Pure. No framework imports, no I/O.

- `AgentAction` — identity, timestamp, agent id, kind (read, write, tool call, spawn)
- `Artifact` — something an action produced that another action could consume; carries an `ArtifactId`
- `Consumption` — edge: this action read that artifact. The load-bearing edge
- `Production` — edge: this action produced that artifact
- `PropagationGraph` — accumulated edges, queryable over a window
- `Window` — bounded slice. Coupling is only meaningful per window
- `CouplingEstimate` — k, the counts it came from, the window

Domain services: `GraphBuilder`, `CouplingCalculator`, `DispersionCalculator`
(the second half of the coal-and-exit signal; stub at v1).

### Driving ports (inbound)

```
ObservationIngest
    record_action(action: AgentAction) -> None
    record_production(action_id, artifact: Artifact) -> None
    record_consumption(action_id, artifact_id: ArtifactId) -> None
```
Deliberately dumb. Takes facts, does not interpret them.

```
CouplingQuery
    coupling(window: Window) -> CouplingEstimate
    graph_snapshot(window: Window) -> PropagationGraph
```

### Driven ports (outbound)

```
ArtifactIdentity
    identify(payload: bytes | str, context: dict) -> ArtifactId
```
The hard one. A write and a later read must resolve to the same id or the edge
is never drawn and k reads as zero. Exact-match hashing works for verbatim reuse
and fails the moment an agent paraphrases, summarises, or quotes part of another
agent's output. Assume v1 is exact-match and that this port is where the next
six months live.

```
GraphStore
    append(edge) -> None
    read_window(window: Window) -> Iterable[edge]

Clock
    now() -> Timestamp
```
Clock is injected, never called directly. Generation time is half the model and
the replay adapter has to be able to lie about it.

```
TaskContext
    declared_inputs(agent_id) -> set[ArtifactId] | None
```
Answers "is this read accounted for by the job." Returns None when the system
cannot say, which is most of the time. Null adapter acceptable at v1; the paper
should be honest that this is the weak flank.

```
Reporter
    emit(estimate: CouplingEstimate) -> None
    emit_graph(graph: PropagationGraph) -> None
```

### Adapters for v1

Inbound:
- One framework adapter. Which framework is still open and should be decided by
  what the target reader runs, not by preference.
- **A replay adapter reading a recorded event log.** Deliberately ranked above
  the framework adapter: it is what makes the Zenodo results reproducible by
  someone who does not run your stack, and it is what makes testing possible.

Outbound: in-memory graph store, JSONL file store, stdout reporter, SVG or HTML
graph reporter. The picture is what makes the paper land, so the visualisation
is not dressing.

### Out of scope for v1, state plainly in the README

- No intervention. Nothing blocks, throttles or kills. Measurement only.
- No baseline learning, no anomaly model, no shipped thresholds.
- No semantic artifact matching.
- No distributed or cross-host collection.

### Ground truth scenario

Small, repeatable, known true propagation graph. A benign multi-agent task plus
a variant where one agent's output starts steering the others. Not an attack,
just coupling. The demonstration is the measure recovering the graph.

---

## 9. Tooling split

- **Vaughan, not delegated:** the interceptability check. Can the framework's
  read/write boundary be hooked without forking. Roughly thirty minutes of
  reading framework source. If the answer is no, the whole design changes shape,
  and the failure mode of delegating it is an agent finding a way that
  technically works by quietly forking the framework.
- **Spock (Claude Code):** the core. Coupling calculator, port structure,
  domain. Correctness over ergonomics. Caution: he will implement hexagonal
  properly and will implement whatever ports he is given, so a vague brief
  produces something logically consistent and wrong at the boundary.
- **Cowork:** the surrounding shape. Scenario harness, visualisation, README,
  paper figures. Better where the output is meant to be looked at.

**Projects portability (checked 20 Sep 2026):** a claude.ai project can be
linked or imported into a Cowork project so Cowork sessions draw on its
knowledge; linking does not merge them. Claude Code has a newer unified Projects
rolling out to Pro and Max Claude Code users first, with chat and Cowork to
follow, so whether Spock sees a chat project depends on the rollout. What
carries across is described as project knowledge (files, instructions); whether
chat transcripts travel is not stated. Reliable answer: this file in the repo
root as `docs/architecture.md` works regardless.

---

## 10. Open

- **Repo name.** Should survive the paper title changing.
- **Framework choice.** Audience question, not engineering.
- **What `ArtifactId` actually is.** Exact-match is the v1 answer but the
  decision deserves its own paragraph of reasoning in the repo, because every
  reviewer will push on it.
- **How much real agent-to-agent propagation is verbatim reuse versus
  paraphrase.** Nobody knows this number. Arguably a finding in itself, and it
  determines whether v1 measures anything real.
- **The swarm's negative temperature coefficient.** What property would make
  more activity mechanically produce less propagation.
- **Mimicry.** The known boundary of the coupling measure.
- **"Stop the swarm" means what, exactly.** Kill every agent and the substrate
  still holds every readable artefact they wrote.

---

## Source note

Redfield (diffusion sensing, c. 2002), Mitchell / Hraber / Crutchfield (lambda
critique, c. 1993), Rendell (Turing machine in Life), Thompson (Reflections on
Trusting Trust, 1984). All cited from memory in conversation and **not verified**.
Check every one before it goes near the paper.
