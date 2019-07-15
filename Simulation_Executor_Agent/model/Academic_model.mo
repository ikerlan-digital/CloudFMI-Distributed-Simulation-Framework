model modelo_simple
import SI = Modelica.SIunits;
parameter SI.Mass M1 = 10 "Mass of first mass"; 
parameter SI.Mass M2 = 20 "Mass of second mass"; 
parameter SI.Mass M3 = 50 "Mass of third mass"; 
parameter SI.Mass M4 = 100 "Mass of fourth mass"; 
parameter SI.Mass M5 = 80 "Mass of fifth mass"; 
parameter SI.Position s0_1 = 0.01 "initial position of first mass"; 
parameter SI.Position s0_2 = 0.015 "initial position of second mass"; 
parameter SI.Position s0_3 = 0.01 "initial position of third mass"; 
parameter SI.Position s0_4 = 0.02 "initial position of fourth mass"; 
parameter SI.Position s0_5 = 0.022 "initial position of fifth mass"; 
parameter SI.TranslationalSpringConstant C_spring = 1000 "Spring-damper stiffness";
parameter SI.TranslationalDampingConstant D_damper = 0.1 "Spring-damper damping";
output SI.Position s1 = mass1.s "position of first mass";
output SI.Velocity v1 = mass1.v "velocity of first mass";
output SI.Acceleration a1 = mass1.a "acceleration of first mass";
output SI.Force F1 = springDamper1.f "force of first spring-damper";
output SI.Position s2 = mass2.s "position of second mass";
output SI.Velocity v2 = mass2.v "velocity of second mass";
output SI.Acceleration a2 = mass2.a "acceleration of second mass";
output SI.Force F2 = springDamper2.f "force of second spring-damper";
output SI.Position s3 = mass3.s "position of third mass";
output SI.Velocity v3 = mass3.v "velocity of third mass";
output SI.Acceleration a3 = mass3.a "acceleration of third mass";
output SI.Force F3 = springDamper3.f "force of third spring-damper";
output SI.Position s4 = mass4.s "position of fourth mass";
output SI.Velocity v4 = mass4.v "velocity of fourth mass";
output SI.Acceleration a4 = mass4.a "acceleration of fourth mass";
output SI.Force F4 = springDamper4.f "force of fourth spring-damper";
output SI.Position s5 = mass5.s "position of fifth mass";
output SI.Velocity v5 = mass5.v "velocity of fifth mass";
output SI.Acceleration a5 = mass5.a "acceleration of fifth mass";
output SI.Force F5  = springDamper5.f "force of fifth spring-damper";
  Modelica.Mechanics.Translational.Components.Fixed fixed annotation(
    Placement(visible = true, transformation(origin = {-138, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.SpringDamper springDamper1(c = C_spring, d = D_damper)  annotation(
    Placement(visible = true, transformation(origin = {-118, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.SpringDamper springDamper2(c = C_spring, d = D_damper) annotation(
    Placement(visible = true, transformation(origin = {-64, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.SpringDamper springDamper3(c = C_spring, d = D_damper) annotation(
    Placement(visible = true, transformation(origin = {-10, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.SpringDamper springDamper4(c = C_spring, d = D_damper) annotation(
    Placement(visible = true, transformation(origin = {48, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.Mass mass1(m = M1, s(fixed = true, start = s0_1))  annotation(
    Placement(visible = true, transformation(origin = {-90, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.Mass mass2(m = M2, s(fixed = true, start = s0_2)) annotation(
    Placement(visible = true, transformation(origin = {-38, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.Mass mass3(m = M3, s(fixed = true, start = s0_3)) annotation(
    Placement(visible = true, transformation(origin = {18, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.Mass mass4(m = M4, s(fixed = true, start = s0_4)) annotation(
    Placement(visible = true, transformation(origin = {76, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.SpringDamper springDamper5(c = C_spring, d = D_damper) annotation(
    Placement(visible = true, transformation(origin = {104, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Translational.Components.Mass mass5(m = M5, s(fixed = true, start = s0_5)) annotation(
    Placement(visible = true, transformation(origin = {132, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
equation
  connect(springDamper5.flange_b, mass5.flange_a) annotation(
    Line(points = {{114, 6}, {122, 6}, {122, 6}, {122, 6}}, color = {0, 127, 0}));
  connect(mass4.flange_b, springDamper5.flange_a) annotation(
    Line(points = {{86, 6}, {92, 6}, {92, 6}, {94, 6}}, color = {0, 127, 0}));
  connect(springDamper4.flange_b, mass4.flange_a) annotation(
    Line(points = {{58, 6}, {54, 6}, {54, 6}, {64, 6}, {64, 6}, {64, 6}, {64, 6}, {66, 6}}, color = {0, 127, 0}));
  connect(springDamper3.flange_b, mass3.flange_a) annotation(
    Line(points = {{0, 6}, {4, 6}, {4, 6}, {10, 6}, {10, 6}, {8, 6}, {8, 6}}, color = {0, 127, 0}));
  connect(mass3.flange_b, springDamper4.flange_a) annotation(
    Line(points = {{28, 6}, {36, 6}, {36, 6}, {38, 6}}, color = {0, 127, 0}));
  connect(springDamper2.flange_b, mass2.flange_a) annotation(
    Line(points = {{-54, 6}, {-53, 6}, {-53, 6}, {-50, 6}, {-50, 6}, {-56, 6}, {-56, 6}, {-48, 6}}, color = {0, 127, 0}));
  connect(mass2.flange_b, springDamper3.flange_a) annotation(
    Line(points = {{-28, 6}, {-22, 6}, {-22, 6}, {-22, 6}, {-22, 6}, {-20, 6}}, color = {0, 127, 0}));
  connect(springDamper1.flange_b, mass1.flange_a) annotation(
    Line(points = {{-108, 6}, {-100, 6}, {-100, 6}, {-100, 6}}, color = {0, 127, 0}));
  connect(mass1.flange_b, springDamper2.flange_a) annotation(
    Line(points = {{-80, 6}, {-76, 6}, {-76, 6}, {-74, 6}}, color = {0, 127, 0}));
  connect(fixed.flange, springDamper1.flange_a) annotation(
    Line(points = {{-138, 6}, {-128, 6}}, color = {0, 127, 0}));
  annotation(
    Icon(coordinateSystem(grid = {0, 0}, extent = {{-150, -50}, {150, 50}})),
    Diagram(coordinateSystem(grid = {0, 0}, extent = {{-150, -50}, {150, 50}})),
    uses(Modelica(version = "3.2.2")),
  version = "",
  __OpenModelica_commandLineOptions = "");
end modelo_simple;
