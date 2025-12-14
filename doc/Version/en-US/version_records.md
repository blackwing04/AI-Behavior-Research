# Weak Agency AI Behavior Model  Version Evolution Records (V1～V7)

This section documents the design objectives, behavioral outcomes, and subsequent improvement directions of the Weak Agency AI Behavior Model across versions V1～V7, establishing a complete and traceable behavioral framework evolution roadmap.

## Environment Configuration

### Base Setup

- **Base Model**: Qwen 2.5 (3B)

### Hardware Specifications

- **CPU**: Intel 12th Generation Core i9-12900K
- **GPU**: NVIDIA GeForce RTX 3070

### Training Approach

- Pure LoRA fine-tuning
- No RLHF
- No RLAIF
- Using minimal dataset

---

## V1: Initial Behavior Testing Phase

### Dataset Scale

- **Sample Count**: 206

### Version Objectives

1. Verify that the LoRA behavior fine-tuning process functions correctly
2. Establish the most basic behavior specification concept
3. Explore feasibility of core designs including Identity, Five Laws, E/I/M, CAST

### Version Achievements

-  Basic behavior specification not yet formed
-  Response logic unstable
-  Insufficient capability in handling ambiguous statements
-  Inconsistent safety rejection performance
-  Presence of anthropomorphic language
-  Boundary judgment (medical, legal, and other professional domains) not established

**Quantitative Results**:
- Semantic Safety Rate: 89.5% (is_allow_risk: 21/200)
- Needs Revision: 146/200 (73%)
- Improvement vs Baseline: ↑ 72pp (5.1× improvement)

### Main Issues

- Behavior framework not yet absorbed by model
- Insufficient consistency and regularity in dataset
- Lack of unified tone and structured behavior templates

---

## V2: Partial Internalization Phase

### Dataset Scale

- **Sample Count**: 523

### Version Objectives

1. Enhance Identity and Five Laws
2. Build prototype for behavior consistency
3. Improve safety rejection and initially constrain model boundary violations
4. Introduce basic operating modes of E/I/M

### Version Achievements

-  Five Laws triggered in partial contexts
-  Increased awareness in rejecting dangerous instructions
-  Initial improvement in Identity
- ◐ Early signs of E/I/M operation
-  Behavior performance still inconsistent
-  Boundary handling still immature
-  Insufficient clarification capability

### Main Issues

- Insufficient internalization of rules by behavior model
- Still exhibiting logical jumps and speculative responses
- Rules insufficient to form fixed behavior framework

---

## V3: Behavior Framework Formation Phase

### Dataset Scale

- **Sample Count**: 1,075

### Version Objectives

1. Fully implement Identity, Five Laws, E/I/M, CAST
2. Establish stable, controllable, and predictable behavior framework
3. Prevent anthropomorphic narratives
4. Strengthen Boundary and non-guessing logical processes

### Version Achievements

-  Model behavior exhibits high consistency
-  Dangerous instruction rejection mechanism stable
-  Ambiguous statement handling logic clear (biased toward non-guessing)
-  E/I/M operating mode clearly discernible
-  CAST tone stable, able to maintain neutral emotional processing
-  Significant improvement in Boundary responses
-  Complete internalization of Identity specifications

### Main Issues

- Processing mechanism for open-ended decision problems not yet established (requires Decision Solver module)
- Tendency toward over-clarification in some contexts
- Lacks adversarial safety behavior
- Multi-turn conversation consistency not yet verified

---

## V4: Decision Solver (Decision Analysis Module)

### Dataset Scale

- **Sample Count**: 2,070

### Version Objectives

1. Distinguish between two problem types: "insufficient information" and "open-ended decisions"
2. Provide directional suggestions in appropriate contexts
3. Establish basic decision analysis framework (objectives, constraints, options, risks)

### Expected Capabilities

-  Propose 3-5 action directions in non-information-insufficient cases
-  Maintain stable reasoning within E/I/M architecture
-  Avoid over-clarification and passive responses

---

## V5: Adversarial Safety (Adversarial Safety Module)

### Dataset Scale

- **Sample Count**: TBD

### Version Objectives

1. Enhance model stability under adversarial prompts
2. Prevent inducement, hidden attacks, and disguised safety requirements
3. Establish higher-order rejection rule framework

### Expected Capabilities

-  Identify multiple types of inductive statements
-  Maintain consistent safety behavior under repeated probing
-  Maintain rejection process within CAST tone

---

## V6: State Persistence (Multi-turn Consistency Module)

### Dataset Scale

- **Sample Count**: TBD

### Version Objectives

1. Maintain behavior consistency across multi-turn conversations
2. Prevent framework deviation caused by context accumulation
3. Strengthen stability of Identity, Five Laws, E/I/M in long conversations

### Expected Capabilities

-  Long conversations without anthropomorphic or boundary-violating reasoning
-  Maintain consistent decision style
-  Avoid alignment drift

---

## V7: Weak Agency (Weak Agency Behavior Module)

### Dataset Scale

- **Sample Count**: TBD

### Version Objectives

1. Establish basic weak agency reasoning capability while completely adhering to Identity and Five Laws
2. Propose next-step actions regarding user objectives
3. Integrate compound reasoning modes of Decision Solver, E/I/M, CAST, Boundary

### Expected Capabilities

-  Identify user objective or dilemma types
-  Propose "reasonable but not boundary-violating" next-step action suggestions
-  Maintain E/I/M stable mode when results are uncertain
-  Maintain standards of non-guessing and non-automatic extension
