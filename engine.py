import pygame
from pygame.locals import (QUIT, KEYDOWN, K_ESCAPE, MOUSEBUTTONDOWN, MOUSEBUTTONUP, \
    K_RIGHT, K_LEFT, K_UP, K_DOWN, K_r, K_s, K_p)

from Box2D import b2Filter
from Box2D.b2 import (world, polygonShape, staticBody, dynamicBody, circleShape, \
    fixtureDef, transform, revoluteJoint)

from uuid import uuid4

class Engine(object):
    def __init__(self, ppm=20, fps=60, width=640, height=480, gravity=(0, 0), caption="Window"):
        pygame.init()
        self.ppm = ppm # pixels per meter
        self.width = width
        self.height = height
        self.colors = {staticBody: (128, 128, 128, 255), dynamicBody: (255, 255, 255, 255), 'joint': (255, 0, 0, 255)}
        self.fps = fps
        self.timestep = 1.0 / self.fps
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.width, self.height), 0, 32)
        self.world = world(gravity=gravity, doSleep=False)
        self.mouse = (0, 0)
        pygame.display.set_caption(caption)

    def to_pybox2d(self, p):
        return [p[0]/self.ppm, (self.height-p[1])/self.ppm]

    def size_to_pybox2d(self, s):
        return (s[0]/self.ppm, s[1]/self.ppm)

    def to_screen(self, p):
        return [p[0]*self.ppm, self.height-p[1]*self.ppm]

    def render(self):
        self.screen.fill((0, 0, 0))
        for body in self.world.bodies:
            for fixture in body.fixtures:
                shape = fixture.shape
                if isinstance(shape, polygonShape):
                    vertices = [(body.transform * v) * self.ppm for v in shape.vertices]
                    vertices = [(v[0], self.height - v[1]) for v in vertices]
                    pygame.draw.polygon(self.screen, self.colors[body.type], vertices, 2)
                elif isinstance(shape, circleShape):
                    pos = self.to_screen(body.position)
                    radius = int(shape.radius * self.ppm)
                    pygame.draw.circle(self.screen, self.colors[body.type], (int(pos[0]), int(pos[1])), radius, 2)
        for joint in self.world.joints:
            p = self.to_screen(joint.anchorA)
            pygame.draw.circle(self.screen, self.colors['joint'], (int(p[0]), int(p[1])), int(.5 * self.ppm), 2)
        pygame.display.flip()

    def step_physics(self, steps=1):
        for i in range(steps):
            self.world.Step(self.timestep, 10, 10)

    def run(self, callback=None, key_pressed=None, mouse_pressed=None, mouse_released=None):
        running = True
        while running:
            self.mouse = pygame.mouse.get_pos()
            for event in self.events():
                if self.quit_event(event):
                    running = False
                    
                if event.type == KEYDOWN:
                    if key_pressed:
                        key_pressed(pygame.key.get_pressed())
                if event.type == MOUSEBUTTONDOWN:
                    if mouse_pressed:
                        mouse_pressed()
                if event.type == MOUSEBUTTONUP:
                    if mouse_released:
                        mouse_released()
            if callback:
                callback()

            self.update()
        self.close()

    def events(self):
        return pygame.event.get()

    def quit_event(self, event):
        return event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE)

    def update(self):
        self.step_physics(1)
        self.render()
        self.clock_tick()

    def clock_tick(self):
        self.clock.tick(self.fps)

    def close(self):
        pygame.quit()

    def add_static_body(self, p, size):
        return self.world.CreateStaticBody(position=self.to_pybox2d(p), shapes=polygonShape(box=self.size_to_pybox2d(size)))

    def bodies_at(self, p):
        p = self.to_pybox2d(p)
        bodies = []
        for body in self.world.bodies:
            if body.fixtures[0].shape.TestPoint(body.transform, p):
                bodies.append(body)
        return bodies

    def body_with_uuid(self, uuid):
        for body in self.world.bodies:
            if body.userData and isinstance(body.userData, dict):
                if body.userData['uuid'] == uuid:
                    return body
        return None

    def add_dynamic_body(self, p, size, angle=0, uuid=None):
        body = self.world.CreateDynamicBody(position=self.to_pybox2d(p), angle=angle)
        body.userData = {}
        uuid = uuid if uuid else str(uuid4())
        body.userData['uuid'] = uuid
        self.set_box(body, size)
        body.linearDamping = 10.0
        body.angularDamping = 10.0
        return body

    def set_box(self, body, size):
        while len(body.fixtures) > 0:
            body.DestroyFixture(body.fixtures[0])
        size = self.size_to_pybox2d(size)
        body.CreatePolygonFixture(box=size, density=1, friction=0.3, filter=b2Filter(groupIndex=-2))
        body.userData['size'] = size

    def add_static_body(self, p, size):
        return self.world.CreateStaticBody(position=self.to_pybox2d(p), shapes=polygonShape(box=self.size_to_pybox2d(size)))

    def pin_at(self, p, a_uuid=None, b_uuid=None):
        bodies = []
        if a_uuid and b_uuid:
            bodies = [self.body_with_uuid(a_uuid), self.body_with_uuid(b_uuid)]
        else:
            bodies = self.bodies_at(p)

        if len(bodies) >= 2:
            b1 = bodies[0]
            b2 = bodies[1]
            joint = self.world.CreateRevoluteJoint(bodyA=b1, bodyB=b2, anchor=self.to_pybox2d(p), 
                maxMotorTorque = 1000.0,
                motorSpeed = 0.0,
                enableMotor = True,
                )
            return joint
        return None

if __name__ == "__main__":
    print('Welcome to the experimental pygame + pybox2d engine!')
    print('- You most likely want to import this as a module')
    print('- and use it to do simple simulations.')

    engine = Engine(caption='Built in run loop', gravity=(0, -30))
    engine.add_static_body((engine.width/2, engine.height-10), (engine.width, 10))
    for i in range(10):
        engine.add_dynamic_body((engine.width/2 + (i-5)*5.0, engine.height/2 + i * 10.0), (10, 10))
    engine.run()