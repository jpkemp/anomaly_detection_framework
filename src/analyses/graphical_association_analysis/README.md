# Graphical Association Analysis for Describing Variation in Surgical Providers
Graphical association analysis uses association rule mining combined with graphs to create a reference model, as well as a model for each provider. <br/>
Provider roles are discovered in the reference model according to the components in the graph. <br/>
Providers can be ranked by the cost of items in their model, but not in their nearest role in the reference model. <br/>

The primary analysis will be presented at MEDINFO 2023 [[1]](#1).
The secondary analysis is presented in the IPhD thesis for which the work was done.

## Test case descriptions
### Primary analysis
#### provider_ranking&#46;py
A model for the nation and for each surgical provider is also created, and a modified graph edit distance is calculated to rank the providers by how much they vary from the national model.

#### ranking_overlap&#46;py
Checks for overlap between provider rankings with the various sensitivity analysis parameters.

### Regional analysis
#### regional_stats&#46;py
Gathers and plots descriptive statistics for the regional data subsets.

#### regional_variation&#64;py
For each geographical region, an association-rule-based graph model is created, and variations in the regions are compared.

## References
<a id="1">[1]</a>
J. Kemp, C. Barker, N. Good, and M. Bain, “Graphical association analysis for identifying variation in provider claims for joint replacement surgery,” in Proceedings of the 19th World Congress on Medical and Health Informatics. Amsterdam, Holland: IOS Press, 2023 (accepted for publication)