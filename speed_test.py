from timeit import timeit
import tinyecs as ecs
import random
from sys import argv

arg = argv[1] if len(argv) == 2 else 'mixed'
if arg not in ['perfect', 'imperfect', 'mixed']:
    arg = "mixed"

WIDTH = 800
HEIGHT = 800
ENTITY_AMOUNT = 1_000 * 4

# TODO: put entities as a list in entity_manager
# Also make the component manager be kept as a reference in the system_manager
# I can insert EntityManager reference into BaseSystem Subclasses using the same method I've used with components nvm i cant lol
# actually add the systems into


class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class Velocity:
    def __init__(self, vec: list[int | float]) -> None:
        self.vec = vec


def ball_physics_system(dt, eid, pos, vel):
    pos.x += vel.vec[0]  # type: ignore
    pos.y += vel.vec[1]  # type: ignore
    if pos.x > WIDTH or pos.x < 0:
        vel.vec[0] *= -1
        if pos.y > HEIGHT or pos.y < 0:
            vel.vec[1] *= -1


def setup(mode):
    tiktok = True
    for _ in range(ENTITY_AMOUNT):
        center = (
            random.randint(0, WIDTH),
            random.randint(0, HEIGHT),
        )
        vel = [
            (random.random() - 0.5) * 400 / 1000,
            (random.random() - 0.5) * 400 / 1000,
        ]
        entity = ecs.create_entity()
        ecs.add_component(entity, Position, Position(*center))
        match mode:
            case 'imperfect':
                pass
            case 'mixed' if tiktok:
                ecs.add_component(entity, Velocity, Velocity(vel))
            case 'perfect':
                ecs.add_component(entity, Velocity, Velocity(vel))
        tiktok = not tiktok


setup(arg)
for e in ecs.eidx.keys():
    ecs.remove_entity(e, postponed=True)
ecs._reap_kill_list()


REPEAT = 1_000

setup(arg)
res = timeit(lambda: ecs.run_system(1, ball_physics_system, Position, Velocity), number=REPEAT)  # type: ignore
print(
    f"Took {res/REPEAT} roughly for each frame, using {len(ecs.eidx)} entities, setting: {arg}"
)
