from isaacsim.core.utils.prims import define_prim, get_prim_at_path
try:
    import isaacsim.storage.native as nucleus_utils
except ModuleNotFoundError:
    import isaacsim.core.utils.nucleus as nucleus_utils
from isaaclab.terrains import TerrainImporterCfg, TerrainImporter
from isaaclab.terrains import TerrainGeneratorCfg
from env.terrain_cfg import HfUniformDiscreteObstaclesTerrainCfg
import omni.replicator.core as rep
import omni.usd
from pxr import Usd, UsdGeom


def remove_floor_debris(root_path="/World/Warehouse",
                        name_keywords=("CardBox",),
                        max_z=1.0,
                        extra_paths=()):
    """Remove clutter the Go2's RL gait snags on and gets stuck in.

    Two ways to target clutter:
      * ``name_keywords`` + ``max_z``: any prim whose name contains a keyword
        and that sits on the floor (low world Z). A box resting on the ground
        has a low Z; boxes stacked on shelves sit higher than ``max_z`` and are
        left in place so the warehouse still looks full.
      * ``extra_paths``: explicit object prim paths to remove outright, for
        one-off props (e.g. a bucket or pushcart) that don't fit the pattern.

    Runs during scene setup, before physics starts, and deactivates matching
    prims (robust for referenced/payload content). Deactivating a prim also
    removes its descendants, so only the outermost match in any branch is
    touched and its Z is read before it is deactivated. Prints what it removed
    so the console shows the count on each launch.
    """
    stage = omni.usd.get_context().get_stage()

    def world_z(prim):
        xform = UsdGeom.Xformable(prim)
        if not xform:
            return None
        return xform.ComputeLocalToWorldTransform(Usd.TimeCode.Default()).ExtractTranslation()[2]

    matched = []
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        if not path.startswith(root_path):
            continue
        if not any(k in prim.GetName() for k in name_keywords):
            continue
        z = world_z(prim)
        if z is not None and z <= max_z:
            matched.append(path)

    # Combine keyword hits with explicit paths, then keep only the outermost
    # prim in each branch (deactivating a parent expires its children's
    # handles). Sort shallow-first and drop any path nested under a kept one.
    targets = sorted(set(matched) | set(extra_paths), key=lambda p: p.count("/"))
    roots = []
    for path in targets:
        if not any(path.startswith(kept + "/") for kept in roots):
            roots.append(path)

    removed = []
    for path in roots:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            z = world_z(prim)
            prim.SetActive(False)
            removed.append((path, z))
    print(f"[sim_env] remove_floor_debris: removed {len(removed)} prim(s) "
          f"(keywords={name_keywords}, z<={max_z}, {len(extra_paths)} explicit):")
    for path, z in removed:
        zs = f"{z:.2f}" if z is not None else "n/a"
        print(f"    {path}  z={zs}")


def add_semantic_label():
    ground_plane = rep.get.prims("/World/GroundPlane")
    with ground_plane:
    # Add a semantic label
        rep.modify.semantics([("class", "floor")])

def create_obstacle_sparse_env():
    add_semantic_label()
    # Terrain
    terrain = TerrainImporterCfg(
        prim_path="/World/obstacleTerrain",
        terrain_type="generator",
        terrain_generator=TerrainGeneratorCfg(
            seed=0,
            size=(50, 50),
            color_scheme="height",
            sub_terrains={"t1": HfUniformDiscreteObstaclesTerrainCfg(
                seed=0,
                size=(50, 50),
                obstacle_width_range=(0.5, 1.0),
                obstacle_height_range=(1.0, 2.0),
                num_obstacles=100 ,
                obstacles_distance=2.0,
                border_width=5,
                avoid_positions=[[0, 0]]
            )},
        ),
        visual_material=None,     
    )
    TerrainImporter(terrain) 

def create_obstacle_medium_env():
    add_semantic_label()
    # Terrain
    terrain = TerrainImporterCfg(
        prim_path="/World/obstacleTerrain",
        terrain_type="generator",
        terrain_generator=TerrainGeneratorCfg(
            seed=0,
            size=(50, 50),
            color_scheme="height",
            sub_terrains={"t1": HfUniformDiscreteObstaclesTerrainCfg(
                seed=0,
                size=(50, 50),
                obstacle_width_range=(0.5, 1.0),
                obstacle_height_range=(1.0, 2.0),
                num_obstacles=200 ,
                obstacles_distance=2.0,
                border_width=5,
                avoid_positions=[[0, 0]]
            )},
        ),
        visual_material=None,     
    )
    TerrainImporter(terrain) 


def create_obstacle_dense_env():
    add_semantic_label()
    # Terrain
    terrain = TerrainImporterCfg(
        prim_path="/World/obstacleTerrain",
        terrain_type="generator",
        terrain_generator=TerrainGeneratorCfg(
            seed=0,
            size=(50, 50),
            color_scheme="height",
            sub_terrains={"t1": HfUniformDiscreteObstaclesTerrainCfg(
                seed=0,
                size=(50, 50),
                obstacle_width_range=(0.5, 1.0),
                obstacle_height_range=(1.0, 2.0),
                num_obstacles=400,
                obstacles_distance=2.0,
                border_width=5,
                avoid_positions=[[0, 0]]
            )},
        ),
        visual_material=None,     
    )
    TerrainImporter(terrain) 

def create_warehouse_env():
    add_semantic_label()
    assets_root_path = nucleus_utils.get_assets_root_path()
    prim = get_prim_at_path("/World/Warehouse")
    prim = define_prim("/World/Warehouse", "Xform")
    asset_path = assets_root_path+"/Isaac/Environments/Simple_Warehouse/warehouse.usd"
    prim.GetReferences().AddReference(asset_path)

def create_warehouse_forklifts_env():
    add_semantic_label()
    assets_root_path = nucleus_utils.get_assets_root_path()
    prim = get_prim_at_path("/World/Warehouse")
    prim = define_prim("/World/Warehouse", "Xform")
    asset_path = assets_root_path+"/Isaac/Environments/Simple_Warehouse/warehouse_with_forklifts.usd"
    prim.GetReferences().AddReference(asset_path)

def create_warehouse_shelves_env():
    add_semantic_label()
    assets_root_path = nucleus_utils.get_assets_root_path()
    prim = get_prim_at_path("/World/Warehouse")
    prim = define_prim("/World/Warehouse", "Xform")
    asset_path = assets_root_path+"/Isaac/Environments/Simple_Warehouse/warehouse_multiple_shelves.usd"
    prim.GetReferences().AddReference(asset_path)

def create_full_warehouse_env():
    add_semantic_label()
    assets_root_path = nucleus_utils.get_assets_root_path()
    prim = get_prim_at_path("/World/Warehouse")
    prim = define_prim("/World/Warehouse", "Xform")
    asset_path = assets_root_path+"/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
    prim.GetReferences().AddReference(asset_path)
    # Clear clutter the Go2 trips on (floor boxes + the cleaning equipment in
    # aisle 2) for a reliable demo.
    remove_floor_debris(extra_paths=(
        "/World/Warehouse/SM_BucketPlastic_B_41",
        "/World/Warehouse/SM_PushcartA_02_22",
    ))

def create_hospital_env():
    add_semantic_label()
    assets_root_path = nucleus_utils.get_assets_root_path()
    prim = get_prim_at_path("/World/Hospital")
    prim = define_prim("/World/Hospital", "Xform")
    asset_path = assets_root_path+"/Isaac/Environments/Hospital/hospital.usd"
    prim.GetReferences().AddReference(asset_path)

def create_office_env():
    add_semantic_label()
    assets_root_path = nucleus_utils.get_assets_root_path()
    prim = get_prim_at_path("/World/Office")
    prim = define_prim("/World/Office", "Xform")
    asset_path = assets_root_path+"/Isaac/Environments/Office/office.usd"
    prim.GetReferences().AddReference(asset_path)