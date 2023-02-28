# Context discovery and cost prediction for detection of anomalous medical claims, with ontology structure providing domain knowledge
This analysis provides a flexible framework for discovering two levels of context within a set of related items, such as orthopaedic procedures, and determining typical costs for providers within each context. <br/>
Providers with unusually high costs can then be flagged for further analysis. <br/>
There were two driving goals behind creation of this framework: improving the cost metric used in the graphical association analysis project, and allowing detection of upcoding from one primary procedure to another (details were presented at HEALTHINF 2023 [[1]](#1)). <br/>
This framework can be easily adapted to other domains utilising item codes, provided an ontology exists and a means of identifying the primary item code can be determined. <br/>
The main analysis takes place in `role_costs.py`, which draws on data constructs and functions in the 'helper_classes' and 'layer_models' folders. <br/>

The process is as follows:
1. Create *patient events* from the raw claims
2. Create *provider episodes* and *ontology episode* pairs from each patient event
3. Identify the *subheading collection* for each episode pair
4. Model the provider roles in each subheading collection
5. Compare episode pair costs to expected costs for the role
6. Rank providers based on the the cost differences for their episodes

## 1. Patient events and episode pairs ##
Data structures built on domain knowledge can help with interpretability and discovering relationships in the data which are useful from a human perspective; good clusters are in the eye of the beholder. <br/>
Patient events create a patient-centred view of a procedure - what claims were made for one patient during a procedure? <br/>

Episodes of care break the patient event down further - what claims did one provider make for that patient during the procedure? <br/>
Episodes of care are a useful construction as they can be aggregated up into a patient-centred view (whether back into patient events, or into a longer-term viw), or into a provider-centred view. <br/>

Episodes of care are split into two constructions in this framework, and may be referred to as episode pairs. <br/>
Provider episodes include the item codes claimed within the episode of care, and are used to find the total cost of the episode of care. <br/>
Ontology episodes convert the item codes in the provider episodes into *ontology locations*, creating a least-generalised view of the items, and are used for role discovery.

## 2. Subheading collections ##
The first level of context discovery is done by grouping patient events (and the associated episode pair). <br/>
For each patient event, the most expensive item code in the group of interest (in this case, orthopaedics items) is assumed to be the primary item. <br/>
The collections are created based on the ontology location of that item. <br/>
This ensures that episodes of care are being appropriately compared to other episodes of care. <br/>
Without generalising to the ontology location (i.e., if episodes were collected together based on their primary item), upcoding from one procedure to another cannot be detected. <br/>
Furthermore, the total number of groups is much larger (each with fewer episodes).
Collecting episodes together based on ontology location worked well for the orthopaedic procedures; alternate methods are possible and may be suitable depending on the domain.

## 3. Role discovery ##
The second level of context is discovered through item code associations within the episodes of care. <br/>
Two methods were trialled for the paper, both producing good results: Graphical Association Analysis (GAA), and Latent Dirchlet Allocation (LDA). <br/>
Other algorithms may also be suitable, particularly topic modelling methods such as Factor Analysis or Non-Negative Matrix Factorisation. <br/>
The discovered topics (components of the graph, in the case of GAA) represent provider roles within the procedure; that is, associations between the delivered services (item codes) can be viewed as describing typical behaviour of a type of provider (such as surgeons, anaesthetists, etc.). <br/>
A model is created for each subheading collection, using the ontology episodes attached to that collection. <br/>
The ontology episodes are used here for two reasons: generalising to the ontology location serves as a dimension reduction technique, grouping items together in a human-interpretable way. <br/>
This means fewer features are required to represent the items. <br/>
Furthermore, it reduces the effect of minor variations (such as varying practices amongst providers regarding choice of item delivery) and focuses on associations between types of services provided, rather than the explicit item codes. <br/>

## 4. Cost evaluation
The costs of each episode of care is calculated by summing the schedule fees of the items in the provider episode. <br/>
A typical cost can then be calculated for each role in each subheading collection; the median is used here, but other metrics may also be suitable.<br/>
A weighted cost difference is calculated for each provider by calculating the difference between their episode costs to the relevant typical cost (with a minimum of 0), and multiplying by the total number of episodes. <br/>
That gives an estimate of the recoverable costs for each provider.

## Supporting analyses
Supporting analyses were conducted to confirm the viability of the results, as described in the paper. <br/>
Result folder locations from each previous analysis file need to be set in the required parameters of supporting files; while somewhat cumbersome, this helps keep the runtime of each analysis short and allows flexibility when trialling different parameters.<br/>
For some analyses a test hash is used to compare several results files using the same parameters; the test hash can be found in the log file.

The supporting analysis files are as follows: <br/>
• `reproducibility.py`: compares multiple LDA runs for sensitivity analysis purposes<br/>
• `lda_gaa_comp.py`: compares the provider ranking from LDA and GAA runs using rank-biased overlap<br/>
• `provider_role_check.py`: finds the roles a provider has episodes assigned to<br/>
• `anomalous_set_comparison.py`: compares the ranking of one run to results of a previous analysis set<br/>
• `psl_providers.py`: gets the derived managed speciality of each provider, and calculates the percentiles of individual claims.<br/>
• `psl_coclaims.py`: calculates the percentiles of coclaims within the dms; this produces the primary output for examining provider claims to a cohort found through a traditional method.<br/>


## References
<a id="1">[1]</a>
J. Kemp, C. Barker, N. Good, and M. Bain, “Context discovery and cost  prediction for detection of anomalous medical claims, with ontology structure providing domain knowledge,” in *Proceedings of the 16th International Joint Conference on Biomedical Engineering Systems and Technologies - Volume 5: HEALTHINF* . California, USA: SCITEPRESS, 2023, pp. 29-40