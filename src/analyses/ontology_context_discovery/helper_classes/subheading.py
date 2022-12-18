from tqdm import tqdm
from src.core.io import config as hc

class Subheading:
    node_labels = []
    def __init__(self, label, add_no_item):
        self.label = label
        self.components: list = []
        self.df_indicies: list = []
        self.episodes: list = []
        self.errors: list = []
        self.fees: list = []
        self.ontologies: list = []
        self.model: dict = None
        self.order: list = []
        self.raw_episodes = []
        self.roles: list = []
        self.role_data: dict = {}
        self.unique_items: set = set()
        self.unique_onts: set = set()
        self.add_no_item: bool = add_no_item

    def add_episode(self, provider, claims):
        onts = claims["Header"].unique().tolist()
        self.unique_onts.update(onts)
        if self.add_no_item and len(onts) == 1:
            onts.append("No other items")
            self.unique_onts.add("No other items")

        cost = claims[hc.COST].sum()
        self.episodes.append(onts)
        self.fees.append(cost)
        self.order.append(provider)

        self.raw_episodes.append(claims[hc.ITEM].values.tolist())
        self.unique_items.update(claims[hc.ITEM].unique().tolist())

    @classmethod
    def find_subheadings(cls, data, add_no_item, primary_header_stems=("3_T8_15")):
        subheadings = {}
        for pat, info in tqdm(data.groupby("EventID")):
            ortho = info[info["Header"].str.startswith(primary_header_stems)]
            assert len(ortho) > 0
            subheading = sorted(ortho.loc[ortho[hc.COST] == ortho[hc.COST].max(), "Header"].unique().tolist())
            # assert len(subheading) == 1 # This fails, need to do something about that
            subheading = subheading[0] # AND THIS
            l = subheadings.get(subheading, Subheading(subheading, add_no_item))
            l.df_indicies = l.df_indicies + info.index.tolist()
            for prov, claims in info.groupby(hc.PR_ID):
                l.add_episode(prov, claims)

            if subheading not in subheadings:
                subheadings[subheading] = l

        return subheadings
