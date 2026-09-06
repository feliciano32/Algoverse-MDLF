PROPOSED EDIT LIST
Paper: Synthetic Lesion Failure Mapping for Chest X-Ray Nodule Detection
Companion to paper_ieee_annotated.md and REVIEW_RESPONSE_MAP.md

Constrained to: abstract at or under 250 words, and total length unchanged at 5 pages.


SPACE BUDGET

Measured from the PDF. Page 5 is the only page with slack: the left column ends at y=414 and the right column at y=258, against a text block running to y=719. That is about 912pt of free column height, roughly 1.4 columns, or about 715 words at this layout's density. Pages 1 through 4 are full.

Everything below is sized to that budget.

  New prose across all additions          755 word-equivalents
  New Figure 4, single column w/ caption  189
  Total demand                            944

  Required cuts (listed at the end)      -244
  Net demand                              700
  Available on page 5                     717
  Margin                                   17

The margin is thin, so the required cuts are not optional. Two reserve cuts are listed if it overruns, and Figure 4 can drop to a single row of four panels to recover roughly 50 more.

Abstract: 232 words currently, 245 in the version below, limit 250.


HOW THIS IS NUMBERED

Paragraphs are numbered P1 onward in reading order, counting figure and table captions as paragraphs. Only paragraphs that change are listed, so the numbering has gaps. A letter suffix (P17a, P22a, P30a, P30b, P36a) marks a new paragraph inserted at that position. Anything in [square brackets] is a value to fill in from your own run.

Section heading change: II. RELATED WORKS becomes II. RELATED WORK. No other heading changes.


P1  ABSTRACT   (245 words)

Models that perform well on common examples tend to fail on underrepresented cases, and in a clinic that gap is dangerous. To address the shortage of rarer cases in chest X-ray datasets, we generate synthetic lesions with controlled attributes using RadEdit, a text-guided diffusion model. We build a grid of nodule images varying along four axes, size, location, contrast, and anatomical overlap, and run a Faster R-CNN detector across the grid to map where it fails. The detector showed high failure rates on spine-overlapping nodules and difficulty detecting small, low-contrast nodules. Using these failure labels we train a BiomedCLIP-based MLP and test whether synthetic failure structure carries over to real failures. Our main result is negative. Failure prediction is far easier in the synthetic domain than the real one: on the QC-passing RadEdit v2 grid the predictor reaches 5-fold AUROC 0.885 plus or minus 0.012, while the analogous real-only NODE21 task reaches 0.667. These are two within-domain separability measurements, not a train-on-synthetic, test-on-real transfer result; transfer is assessed separately, and synthetic failures do not reliably cover real false negatives in feature space. At matched abstention rates the synthetic predictor ties, and never beats, a detector-confidence baseline. DOMINO slice discovery surfaces a coherent failure cluster spanning multiple grid cells, showing the four axes do not capture the whole failure space. Synthetic grids are therefore usable for controlled analysis, but should count as robustness evidence only alongside generator controls and an explicit synthetic-to-real check, a check this grid fails.


P2  INTRODUCTION, FIRST PARAGRAPH

Deep learning systems for chest X-ray analysis have achieved strong performance on benchmark datasets, but they often fail on rare or clinically difficult cases that are typically underrepresented in training datasets [1]. Small nodules, low-contrast lesions, and abnormalities obscured by anatomical structures such as ribs and clavicles remain challenging for many detection models. Because biomedical imaging datasets are expensive and limited in diversity, these failure modes are difficult to study using real data alone.


P4  INTRODUCTION, THIRD PARAGRAPH

In this work, we propose a framework that uses synthetic lung lesions with controlled attributes including size, location, contrast, and anatomical overlap to systematically map where chest X-ray detectors fail. By evaluating detectors across a dense synthetic lesion grid, we construct a failure map that identifies clinically difficult regions of the model's decision space. We then train a lightweight failure predictor on these synthetic failure cases to test whether synthetic failures can support abstention analysis. Our goal is to study whether controlled synthetic lesions can make detector failure modes more visible and measurable.


P5  INTRODUCTION, FOURTH PARAGRAPH

This leads to the question that motivates the paper: does this synthetic failure structure transfer to real detector failures? Our answer is largely negative. Failures are separable on the synthetic grid, but the synthetic predictor does not beat a confidence baseline at matched abstention rates, and synthetic failures do not reliably cover real false negatives in feature space. Rather than an overstated abstention result, we present this gap as the contribution: synthetic and real failure structures differ in measurable ways, and synthetic stress tests must be validated against real failures before being read as evidence of clinical reliability.


P6  INTRODUCTION, CONTRIBUTIONS PARAGRAPH

The slice description in the second half is rewritten to match the metadata in the shipped 40 images. Verify against your own DOMINO output before applying. See REVIEW_RESPONSE_MAP.md item 2. Net cost of the rewrite is about 14 words.

Our contributions are: (1) an attribute-level failure map for a chest X-ray nodule detector built from controlled synthetic lesions, exposing interpretable weaknesses such as high failure rates on spine-overlapping and small low-contrast nodules; (2) a paired within-domain comparison quantifying how much easier failure prediction is on synthetic data than on real data: a predictor trained and evaluated on QC-passing RadEdit v2 failure labels achieved AUROC 0.885, while the analogous predictor trained and evaluated on real NODE21 failures reached only 0.667, a separability gap rather than a transfer result, with no advantage over confidence-based abstention at matched rates; and (3) a slice-discovery analysis revealing a large failure cluster that cuts across the predefined grid cells, showing the attribute grid is a useful but incomplete description of where the detector breaks down. To make these failures legible rather than anecdotal, we run two complementary analyses on the grid: GEORGE-style worst-group ranking over the known attribute groups, and DOMINO [3] slice discovery over BiomedCLIP embeddings. DOMINO surfaces the failure region the attribute axes miss on their own: a coherent 40-image slice, every case a detector failure. The slice skews small (50 percent) and low-contrast (45 percent) and is enriched for upper-right nodules (28 percent), but spans all six locations and all five overlap conditions, with 29 of 40 members involving anatomical overlap. This is evidence that detector failure has structure our predefined grid only partly captures.


P13  TABLE I CAPTION

Version A if you computed confidence intervals and can add them to the table. Version B if you did not, since the current caption asserts overlapping intervals that appear nowhere in the paper.

Version A: TABLE I. NODE21 validation FROC and sensitivity by training augmentation, with 95 percent bootstrap confidence intervals over [N] resamples. Intervals overlap substantially, so the differences are not interpreted as gains or degradation.

Version B: TABLE I. NODE21 validation FROC and sensitivity by training augmentation. Differences are within the range expected from validation-split variance and are not interpreted as gains or degradation.


P17a  METHODS, NEW PARAGRAPH   (100 words)

Insert after the paragraph ending "...the same predictor is trained on real NODE21 failures only." Answers why the real task reaches only 0.667.

The real-only ablation uses the same 5-fold protocol, features, and head, but is trained on the [N] positive NODE21 validation cases, of which [k] are detector failures, roughly an order of magnitude fewer labels than the 161-image grid. The real task is also intrinsically harder: real nodules vary continuously in conspicuity rather than occupying discrete grid levels, and real failures mix missed detections with localization errors, whereas every synthetic failure is a miss of a known inserted lesion. We therefore read 0.667 as evidence that real failure structure is less separable in BiomedCLIP space, not that the predictor is broken.


P21  RESULTS, AUGMENTATION PARAGRAPH

Final sentence assumes Table I version B. With version A, keep your original final sentence and add the intervals to the table instead.

We next evaluated whether synthetic lesion augmentation improved NODE21 performance. Training with RadEdit augmentation produced a FROC of 0.855, copy-paste augmentation produced 0.843, and combined RadEdit plus copy-paste augmentation produced 0.872, compared with 0.883 for the real-only baseline. These differences are within the range expected from validation-split variance, so we do not interpret them as gains or degradation.


P22a  RESULTS, NEW PARAGRAPH   (143 words)

Insert after the paragraph ending "...corresponding to a sensitivity of 19.9 percent." This answers whether 19.9 percent reflects the detector or the generator, using data already in the paper.

The gap between the two arms is informative. Both grids share the same source images, attribute levels, insertion locations, and fixed detector, and differ only in how the lesion is rendered. We therefore attribute much of the 22.3-point difference to generator rendering rather than detector weakness: RadEdit lesions are systematically less conspicuous than real nodules of nominally matched size and contrast. The 19.9 percent figure is thus a joint property of generator and detector, not a detector sensitivity estimate. More importantly, the copy-paste ceiling of 42.2 percent, far below the detector's 88.9 percent validation sensitivity at 0.5 FP/img, indicates that insertion realism bounds achievable sensitivity on both arms. This is the concrete form the synthetic-to-real domain gap takes here, and the reason we treat the failure map as a relative ranking across attribute cells rather than a calibrated estimate of clinical miss rates.


P23  RESULTS, FAILURE PREDICTOR PARAGRAPH

Only apply the leakage-checked wording if that is what "verified evaluation" referred to. If it meant something else, substitute the accurate description or delete the phrase.

Using the QC-passing RadEdit v2 failure labels, we trained a lightweight failure predictor on BiomedCLIP features and detector summary features. Under leakage-checked evaluation, in which no source image appears in both the training and test folds, the synthetic failure predictor achieved a 5-fold cross-validated AUROC of 0.885 plus or minus 0.012, while a shuffled-label control was near random performance. However, a real-only predictor trained on positive NODE21 validation cases achieved AUROC 0.667 plus or minus [x], suggesting that synthetic and real failure structures differ in measurable ways.


P24  FIGURE 2 CAPTION

Fig. 2. There is a large separability gap between the synthetic (0.885) and real (0.667) failure-prediction tasks. Both bars measure within-domain separability; neither is a train-on-synthetic, test-on-real transfer result.


P25  RESULTS, ABSTENTION PARAGRAPHS   (condensed, saves 46 words)

Replaces the two existing abstention paragraphs. Same numbers, fewer words, consistent with the reviewer's view that the abstention result is a non-event.

On the RadEdit v2 synthetic set, the learned predictor did not outperform detector-confidence abstention under exact matched rates: from a no-abstention answered-case failure rate of 0.807, both methods reached 0.786, 0.760, and 0.726 at approximately 10, 20, and 30 percent abstention. The real-only NODE21 ablation was more favorable. From 0.257 without abstention, detector confidence reached 0.144 and 0.089 at 20 and 30 percent abstention, while the real-only predictor reached 0.078 and 0.063.


P27  RESULTS, EXTERNAL CHECK   (condensed, saves 14 words)

Merges the two existing external-check paragraphs.

As a preliminary external check, we ran the NODE21 detector on CheXpert Lung Lesion labels and a report-derived MIMIC-CXR nodule subset. These subsets lack localized boxes, so the analysis is image-level and is not a NODE21-style FROC evaluation. At a score threshold of 0.05 the detector fired on 674/675 CheXpert positives and 1574/1575 negatives, indicating poor specificity; on MIMIC-CXR it fired on 320/450 report-positive and 585/1013 report-negative images (proxy FNR 0.289, proxy FPR 0.577).


P28  FIGURE 3 CAPTION

Fig. 3. Coverage is very threshold sensitive, moving from 0/29 to 29/29 over a narrow range. There is no stable operating threshold, which is the concrete reason global embeddings are insufficient for cross-domain transfer.


P30a  RESULTS, NEW PARAGRAPH   (162 words)

Insert after the paragraph ending "...do not fully explain detector behavior." This is the DOMINO failure case study two reviewers asked for. Adjust the conspicuity claims to what you can support from your own inspection; the structural argument holds regardless and is verifiable from the slice metadata.

Inspecting the slice clarifies what the attribute axes miss. Its 40 members are drawn from 16 source radiographs and span all six location bins and all five overlap conditions, so the cluster is not a relabelling of a single grid cell. What its members share is not an attribute combination but a rendering property: the inserted lesion is typically low in conspicuity relative to surrounding parenchymal and bony texture, including in cases whose nominal size and contrast settings were high. The operative failure variable therefore appears to be realized conspicuity, a joint function of generator, insertion site, and local background, rather than the nominal attribute levels. This is also why the slice is invisible to worst-group analysis: GEORGE can only rank groups the grid defines, whereas conspicuity is latent and cuts across all of them. An attribute grid indexes the requested difficulty of a synthetic case, not its realized difficulty, and the two can diverge enough to relocate the failure region entirely.


P30b  FIGURE 4 CAPTION, NEW   (53 words)

New single-column figure to accompany P30a. Draft layout is in fig4_domino_slice_examples_DRAFT.png; regenerate at print resolution with your own windowing. Budget assumes a single-column figure of about 200pt plus caption. If space runs out, drop to a single row of four panels and recover roughly 50 word-equivalents.

WHERE TO PUT IT

Target: top of page 4, right column, so the figure sits beside the case-study paragraph P30a.

The source placement is not the same as the target, because the earlier additions reflow the page. In the current PDF the DOMINO paragraph sits at page 4, left column, y=339 to 420. Everything added ahead of it nets about +170 words, or 216pt, which pushes that paragraph down to roughly y=555 to 636, near the bottom of the left column. P30a then overflows into the right column. So P30a will begin at the top of page 4's right column, and that is where the figure should be.

LaTeX floats forward, never backward, so place the float source one paragraph EARLIER than the target: immediately before "We also used GEORGE-style worst-group analysis and DOMINO slice discovery...", not after P30a.

  \begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{fig4_domino_slice.pdf}
    \caption{Representative members of the 40-image DOMINO ...}
    \label{fig:domino-slice}
  \end{figure}

Placing it after P30a instead will float it to the top of page 5's left column, a full column away from the text that discusses it. Still legal, just worse.

Alternative, if you want all eight panels legible: a double-column figure* [t] at the top of page 5. Page 5 holds all the free space in the paper (912pt), so this is the one place a wide figure is affordable. The cost is that it lands after the Results text and above the references.

Avoid the bottom of page 4's left column. A [b] float there collides with the V. DISCUSSION heading and pushes it into the next column.

Do not place it near Fig. 3 at the top of page 4's left column. Two failure-analysis figures stacked in one column invites the reader to conflate them, and Fig. 3 is about coverage thresholds, not slice composition.

Numbering takes care of itself: the float source sits after Fig. 3's source, so it becomes Fig. 4 in whichever column it lands.

These positions are estimates from the current PDF's text density. Compile once with all edits in place and check where it actually lands.

Fig. 4. Representative members of the 40-image DOMINO failure slice, with ground-truth box and magnified inset. Every panel is a detector miss. The slice spans small to large lesions, low to high nominal contrast, and four overlap conditions; rendered lesion conspicuity is low throughout, consistent with the generator gap quantified in Section IV.


P33  DISCUSSION, FIRST PARAGRAPH

This work shows that synthetic lesion grids can be useful for studying failure modes in chest X-ray nodule detection, but the synthetic data itself must be interpreted carefully. The NODE21 detector achieved strong overall validation performance, yet the synthetic grid revealed that performance varies substantially across lesion attributes. Small, low-contrast, and overlapping nodules were more difficult for the detector. This supports a central motivation of the project: average performance can hide important weaknesses. By controlling the specific lesion size, contrast, and anatomical overlap, the failure map provides a more structured way to identify where the detector is least reliable.


P34  DISCUSSION, SECOND PARAGRAPH

The results also suggest that synthetic data is more useful here as an evaluation tool than only as augmentation. Training with synthetic lesions did not clearly improve detector performance over the real-only baseline. However, the synthetic images still localized where the detector was unreliable. This distinction is important because synthetic data can still help characterize model behavior and identify blind spots even if it does not improve average detector accuracy substantially.


P35  DISCUSSION, ABSTENTION PARAGRAPH   (condensed, saves 42 words)

The abstention experiments give a more limited result. The synthetic predictor did not outperform detector-confidence abstention at any matched rate, while the real-only ablation did, suggesting real failure labels remain important for training reliable deferral models.


P36a  DISCUSSION, NEW PARAGRAPH   (200 words)

Insert immediately before "There are a few key limitations to note." This is the deeper argument for why the negative result matters, condensed from three paragraphs to one to fit the page budget.

It is worth stating why a negative result of this shape matters. This is not a null result in the ordinary sense, where an intervention fails to help. It is a case where the synthetic evaluation returns a confidently structured answer that the real data does not corroborate: 0.885 AUROC with a shuffled-label control near chance, stable across folds, and accompanied by an interpretable attribute-level failure map. Reported alone, as synthetic stress tests routinely are, that would read as evidence that this detector's failure modes are understood. Because within-domain separability on synthetic data is easy to achieve and easy to mistake for robustness evidence, we argue it should not be reported as such without three checks: a positive control isolating generator rendering from detector weakness, in our case copy-paste insertion at 42.2 percent against RadEdit's 19.9 percent on an otherwise identical grid; a within-domain real baseline for the same task; and a transfer or coverage test with a sensitivity analysis over its free parameters. Our grid passes the first and fails the other two. That is worth knowing, and knowable only because the checks were run; the cost of omitting them is not a missed insight but a false one.


P37  DISCUSSION, LIMITATIONS PARAGRAPH

There are a few key limitations to note. First, and most importantly, the failure map is confounded with generator fidelity. The copy-paste positive control makes the size of this effect concrete: the same detector, source images, and attribute grid reach 42.2 percent sensitivity on real inserted patches and 19.9 percent on diffusion-rendered ones. The 19.9 percent figure therefore characterizes the generator-detector pair, not the detector, and absolute miss rates from this grid should not be read as clinical sensitivity estimates. A radiologist conspicuity rating of a stratified subsample would separate generator under-rendering from detector weakness directly, and is the necessary next step before such rates are reported as clinical findings. Second, although the failure map was designed around clinically motivated attributes, it cannot represent the full range of difficult cases encountered in practice. DOMINO suggests that some failure structure falls outside the predefined grid, so stronger validation with localized external annotations and radiologist review is needed before making broader clinical reliability claims.


P38  CONCLUSION

Synthetic lesion grids revealed systematic failure patterns in a chest X-ray detector, but the key finding is their disconnect from real detector failures. On the QC-passing RadEdit v2 synthetic grid, the failure predictor achieved 0.885 AUROC under 5-fold cross-validation; on real NODE21 data, the corresponding failure-prediction task reached 0.667 AUROC. Both are within-domain measurements; the gap indicates that real failure structure is less separable in this feature space than synthetic failure structure, and is not itself a transfer result. Transfer is assessed separately by the coverage analysis, which reinforced the same conclusion: synthetic failure cases did not reliably overlap with real hard cases in feature space, and the overlap was unstable across distance thresholds, suggesting global embeddings are insufficient for cross-domain transfer. Confidence-baseline abstention matched the synthetic predictor at every reported operating point and was never outperformed by it, further demonstrating that synthetic failure labels do not transfer directly to real detection decisions. Worst-group and slice-discovery analyses revealed that detector failures concentrated in interpretable subgroups defined by lesion attributes, but also that latent failure slices cut across the predefined grid, indicating that the synthetic design space is useful but incomplete. This work demonstrates that synthetic failure mapping is a legitimate auditing tool, but only when paired with validation against real data. Synthetic stress tests can create the appearance of robustness without capturing deployed failure modes. For chest X-ray AI moving toward clinical use, this means synthetic grids help identify possible blind spots, but real external validation with localized annotations remains essential before deployment claims are credible.


REQUIRED CUTS

These are not optional. Without them the additions overrun by roughly half a column. Total saving is 244 words.

CUT 1, saves 93 words. Delete the fourth Discussion paragraph in full, beginning "Overall, this project shows that RadEdit-based synthetic lesion testing can help identify where a chest X-ray detector is most likely to fail" and ending "before making stronger claims about clinical use." Every claim in it is made again in the Conclusion, mostly in the same order. This is the cleanest 93 words in the paper to lose and it costs no content.

CUT 2, saves 49 words. Replace the second Related Work paragraph with:

Synthetic medical image generation addresses limited data and rare clinical findings. Synthetic nodule benchmarks use generated lung nodules with controlled attributes to evaluate detection behavior, while RadEdit uses diffusion-based image editing to create distribution shifts and stress-test medical vision models [2]. RadEdit is especially relevant here because it edits existing chest X-rays using masks and text prompts, making it possible to insert abnormalities into targeted regions. However, generated lesions must be interpreted carefully, because a detector miss may reflect generator quality, localization, or visual realism rather than only detector weakness.

CUT 3, saves 46 words. Already applied above as P25.

CUT 4, saves 42 words. Already applied above as P35.

CUT 5, saves 14 words. Already applied above as P27.


RESERVE CUTS

Only if the layout overruns after the above.

RESERVE 1, saves about 45 words. The Discussion's second paragraph, P34, overlaps substantially with the new P36a, which now makes the same evaluation-versus-augmentation point more sharply. It can be reduced to its first and last sentences.

RESERVE 2, saves about 40 words. The Introduction's fourth paragraph, P5, previews the contributions paragraph P6 almost claim for claim. Its middle two sentences can go without loss.

RESERVE 3, saves about 50 word-equivalents. Reduce Figure 4 from two rows of four panels to one row of four.


SUMMARY

Rewritten to fix the transfer misreading: P1, P6, P24, P38
Rewritten to match the shipped slice metadata, pending verification: P6
New material answering reviewer requests: P17a, P22a, P30a, P30b, P36a
Rewritten to quantify the 19.9 percent domain gap: P37
Caption and claim corrections: P13, P21, P23, P28
Condensed to pay for the additions: P25, P27, P35, plus Cuts 1 and 2
Wording and grammar only: P2, P4, P5, P33, P34

Values still to supply: N and k in P17a, the confidence interval in P23, the resample count in P13 version A.

A note on the estimates. Word-equivalents assume about 525 words per full column at this layout's density, measured from the current text. Treat the 17-word margin as within noise: compile once with the additions and the required cuts in place, then use the reserve cuts if page 6 appears.
