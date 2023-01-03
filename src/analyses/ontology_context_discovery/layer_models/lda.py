'''Template for data analyses'''
from overrides import overrides
from gensim import corpora
from gensim.models import LdaModel
from src.analyses.ontology_context_discovery.helper_classes.role import Role
from src.analyses.ontology_context_discovery.layer_models.base import AbstractLayerModel

class LdaRoles(AbstractLayerModel):
    '''Data analysis base class'''
    @overrides
    def create_role_data(test_case, log, label, subheadings, seed=None) -> None:
        s = subheadings
        num_topics = 5
        corp_map = corpora.Dictionary(s.episodes)
        docs = [corp_map.doc2bow(ep) for ep in s.episodes]
        if seed is None:
            lda = LdaModel(corpus=docs, id2word=corp_map, eval_every=None, num_topics=num_topics)
        else:
            lda = LdaModel(corpus=docs, id2word=corp_map, eval_every=None, num_topics=num_topics, random_state=seed)

        s.model = lda
        log(f"Topics for subheading {label}")
        log(lda.print_topics(num_topics=6, num_words=10))

        s.role_data = {r: Role(r) for r in range(num_topics + 1)}
        for i, ep in enumerate(s.episodes):
            role_prediction = lda[corp_map.doc2bow(ep)]
            role = sorted(role_prediction, key=lambda x: x[1], reverse=True)[0][0]
            s.roles.append(role)
            s.role_data[role].fees.append(s.fees[i])
