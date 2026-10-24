wipe
model BasicBuilder -ndm 3 -ndf 6
section ElasticMembranePlateSection 1 30000000000.0 0.3 0.04 0
node 1 0.0 0.0 0
fix 1 1 1 1 0 0 1
node 2 1.0 0.0 0
fix 2 1 1 1 0 0 1
node 3 2.0 0.0 0
fix 3 1 1 1 0 0 1
node 4 3.0 0.0 0
fix 4 1 1 1 0 0 1
node 5 4.0 0.0 0
fix 5 1 1 1 0 0 1
node 6 0.0 1.0 0
fix 6 1 1 1 0 0 1
node 7 1.0 1.0 0
fix 7 1 1 0 0 0 1
node 8 2.0 1.0 0
fix 8 1 1 0 0 0 1
node 9 3.0 1.0 0
fix 9 1 1 0 0 0 1
node 10 4.0 1.0 0
fix 10 1 1 1 0 0 1
node 11 0.0 2.0 0
fix 11 1 1 1 0 0 1
node 12 1.0 2.0 0
fix 12 1 1 0 0 0 1
node 13 2.0 2.0 0
fix 13 1 1 0 0 0 1
node 14 3.0 2.0 0
fix 14 1 1 0 0 0 1
node 15 4.0 2.0 0
fix 15 1 1 1 0 0 1
node 16 0.0 3.0 0
fix 16 1 1 1 0 0 1
node 17 1.0 3.0 0
fix 17 1 1 0 0 0 1
node 18 2.0 3.0 0
fix 18 1 1 0 0 0 1
node 19 3.0 3.0 0
fix 19 1 1 0 0 0 1
node 20 4.0 3.0 0
fix 20 1 1 1 0 0 1
node 21 0.0 4.0 0
fix 21 1 1 1 0 0 1
node 22 1.0 4.0 0
fix 22 1 1 1 0 0 1
node 23 2.0 4.0 0
fix 23 1 1 1 0 0 1
node 24 3.0 4.0 0
fix 24 1 1 1 0 0 1
node 25 4.0 4.0 0
fix 25 1 1 1 0 0 1
element ShellMITC4 1 1 2 7 6 1
element ShellMITC4 2 2 3 8 7 1
element ShellMITC4 3 3 4 9 8 1
element ShellMITC4 4 4 5 10 9 1
element ShellMITC4 5 6 7 12 11 1
element ShellMITC4 6 7 8 13 12 1
element ShellMITC4 7 8 9 14 13 1
element ShellMITC4 8 9 10 15 14 1
element ShellMITC4 9 11 12 17 16 1
element ShellMITC4 10 12 13 18 17 1
element ShellMITC4 11 13 14 19 18 1
element ShellMITC4 12 14 15 20 19 1
element ShellMITC4 13 16 17 22 21 1
element ShellMITC4 14 17 18 23 22 1
element ShellMITC4 15 18 19 24 23 1
element ShellMITC4 16 19 20 25 24 1
timeSeries Linear 1
pattern Plain 1 1 {
load 1 0 0 -25.0 0 0 0
load 2 0 0 -50.0 0 0 0
load 7 0 0 -100.0 0 0 0
load 6 0 0 -50.0 0 0 0
load 3 0 0 -50.0 0 0 0
load 8 0 0 -100.0 0 0 0
load 4 0 0 -50.0 0 0 0
load 9 0 0 -100.0 0 0 0
load 5 0 0 -25.0 0 0 0
load 10 0 0 -50.0 0 0 0
load 12 0 0 -100.0 0 0 0
load 11 0 0 -50.0 0 0 0
load 13 0 0 -100.0 0 0 0
load 14 0 0 -100.0 0 0 0
load 15 0 0 -50.0 0 0 0
load 17 0 0 -100.0 0 0 0
load 16 0 0 -50.0 0 0 0
load 18 0 0 -100.0 0 0 0
load 19 0 0 -100.0 0 0 0
load 20 0 0 -50.0 0 0 0
load 22 0 0 -50.0 0 0 0
load 21 0 0 -25.0 0 0 0
load 23 0 0 -50.0 0 0 0
load 24 0 0 -50.0 0 0 0
load 25 0 0 -25.0 0 0 0
}
constraints Plain
numberer RCM
system BandGeneral
algorithm Linear
integrator LoadControl 1
analysis Static
if {[analyze 1] != 0} {exit 2}
reactions
set f [open values.tsv w]
puts $f [nodeDisp 13 3]
puts $f [nodeReaction 1 3]
puts $f [nodeReaction 2 3]
puts $f [nodeReaction 7 3]
puts $f [nodeReaction 6 3]
puts $f [nodeReaction 3 3]
puts $f [nodeReaction 8 3]
puts $f [nodeReaction 4 3]
puts $f [nodeReaction 9 3]
puts $f [nodeReaction 5 3]
puts $f [nodeReaction 10 3]
puts $f [nodeReaction 12 3]
puts $f [nodeReaction 11 3]
puts $f [nodeReaction 13 3]
puts $f [nodeReaction 14 3]
puts $f [nodeReaction 15 3]
puts $f [nodeReaction 17 3]
puts $f [nodeReaction 16 3]
puts $f [nodeReaction 18 3]
puts $f [nodeReaction 19 3]
puts $f [nodeReaction 20 3]
puts $f [nodeReaction 22 3]
puts $f [nodeReaction 21 3]
puts $f [nodeReaction 23 3]
puts $f [nodeReaction 24 3]
puts $f [nodeReaction 25 3]
close $f
exit 0