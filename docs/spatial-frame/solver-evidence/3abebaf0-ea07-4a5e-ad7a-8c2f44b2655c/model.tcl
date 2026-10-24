wipe
model BasicBuilder -ndm 3 -ndf 6
node 1 0 0 0
fix 1 1 1 1 1 1 1
node 2 4 0 0
fix 2 1 1 1 1 1 1
node 3 8 0 0
fix 3 1 1 1 1 1 1
node 4 0 4 0
fix 4 1 1 1 1 1 1
node 5 4 4 0
fix 5 1 1 1 1 1 1
node 6 8 4 0
fix 6 1 1 1 1 1 1
node 7 0 0 3
node 8 4 0 3
node 9 8 0 3
node 10 0 4 3
node 11 4 4 3
node 12 8 4 3
node 13 0 0 6
node 14 4 0 6
node 15 8 0 6
node 16 0 4 6
node 17 4 4 6
node 18 8 4 6
geomTransf Linear 1 0 1 0
element elasticBeamColumn 1 1 7 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 1
geomTransf Linear 2 0 1 0
element elasticBeamColumn 2 2 8 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 2
geomTransf Linear 3 0 1 0
element elasticBeamColumn 3 3 9 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 3
geomTransf Linear 4 0 1 0
element elasticBeamColumn 4 4 10 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 4
geomTransf Linear 5 0 1 0
element elasticBeamColumn 5 5 11 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 5
geomTransf Linear 6 0 1 0
element elasticBeamColumn 6 6 12 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 6
geomTransf Linear 7 0 0 1
element elasticBeamColumn 7 7 8 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 7
geomTransf Linear 8 0 0 1
element elasticBeamColumn 8 8 9 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 8
geomTransf Linear 9 0 0 1
element elasticBeamColumn 9 10 11 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 9
geomTransf Linear 10 0 0 1
element elasticBeamColumn 10 11 12 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 10
geomTransf Linear 11 0 0 1
element elasticBeamColumn 11 7 10 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 11
geomTransf Linear 12 0 0 1
element elasticBeamColumn 12 8 11 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 12
geomTransf Linear 13 0 0 1
element elasticBeamColumn 13 9 12 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 13
geomTransf Linear 14 0 1 0
element elasticBeamColumn 14 7 13 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 14
geomTransf Linear 15 0 1 0
element elasticBeamColumn 15 8 14 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 15
geomTransf Linear 16 0 1 0
element elasticBeamColumn 16 9 15 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 16
geomTransf Linear 17 0 1 0
element elasticBeamColumn 17 10 16 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 17
geomTransf Linear 18 0 1 0
element elasticBeamColumn 18 11 17 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 18
geomTransf Linear 19 0 1 0
element elasticBeamColumn 19 12 18 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 19
geomTransf Linear 20 0 0 1
element elasticBeamColumn 20 13 14 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 20
geomTransf Linear 21 0 0 1
element elasticBeamColumn 21 14 15 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 21
geomTransf Linear 22 0 0 1
element elasticBeamColumn 22 16 17 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 22
geomTransf Linear 23 0 0 1
element elasticBeamColumn 23 17 18 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 23
geomTransf Linear 24 0 0 1
element elasticBeamColumn 24 13 16 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 24
geomTransf Linear 25 0 0 1
element elasticBeamColumn 25 14 17 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 25
geomTransf Linear 26 0 0 1
element elasticBeamColumn 26 15 18 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999982 0.00067499999999999982 26
timeSeries Linear 1
pattern Plain 1 1 {
eleLoad -ele 7 -type -beamUniform 0 -10000 0
eleLoad -ele 8 -type -beamUniform 0 -10000 0
eleLoad -ele 9 -type -beamUniform 0 -10000 0
eleLoad -ele 10 -type -beamUniform 0 -10000 0
eleLoad -ele 20 -type -beamUniform 0 -10000 0
eleLoad -ele 21 -type -beamUniform 0 -10000 0
eleLoad -ele 22 -type -beamUniform 0 -10000 0
eleLoad -ele 23 -type -beamUniform 0 -10000 0
}
constraints Plain
numberer RCM
system BandGeneral
algorithm Linear
integrator LoadControl 1
analysis Static
if {[analyze 1] != 0} {exit 2}
reactions
set out [open nodes.tsv w]
puts $out "1 [nodeDisp 1]"
puts $out "2 [nodeDisp 2]"
puts $out "3 [nodeDisp 3]"
puts $out "4 [nodeDisp 4]"
puts $out "5 [nodeDisp 5]"
puts $out "6 [nodeDisp 6]"
puts $out "7 [nodeDisp 7]"
puts $out "8 [nodeDisp 8]"
puts $out "9 [nodeDisp 9]"
puts $out "10 [nodeDisp 10]"
puts $out "11 [nodeDisp 11]"
puts $out "12 [nodeDisp 12]"
puts $out "13 [nodeDisp 13]"
puts $out "14 [nodeDisp 14]"
puts $out "15 [nodeDisp 15]"
puts $out "16 [nodeDisp 16]"
puts $out "17 [nodeDisp 17]"
puts $out "18 [nodeDisp 18]"
close $out
set out [open reactions.tsv w]
puts $out "1 [nodeReaction 1]"
puts $out "2 [nodeReaction 2]"
puts $out "3 [nodeReaction 3]"
puts $out "4 [nodeReaction 4]"
puts $out "5 [nodeReaction 5]"
puts $out "6 [nodeReaction 6]"
puts $out "7 [nodeReaction 7]"
puts $out "8 [nodeReaction 8]"
puts $out "9 [nodeReaction 9]"
puts $out "10 [nodeReaction 10]"
puts $out "11 [nodeReaction 11]"
puts $out "12 [nodeReaction 12]"
puts $out "13 [nodeReaction 13]"
puts $out "14 [nodeReaction 14]"
puts $out "15 [nodeReaction 15]"
puts $out "16 [nodeReaction 16]"
puts $out "17 [nodeReaction 17]"
puts $out "18 [nodeReaction 18]"
close $out
set out [open forces.tsv w]
puts $out "1 [eleResponse 1 localForce]"
puts $out "2 [eleResponse 2 localForce]"
puts $out "3 [eleResponse 3 localForce]"
puts $out "4 [eleResponse 4 localForce]"
puts $out "5 [eleResponse 5 localForce]"
puts $out "6 [eleResponse 6 localForce]"
puts $out "7 [eleResponse 7 localForce]"
puts $out "8 [eleResponse 8 localForce]"
puts $out "9 [eleResponse 9 localForce]"
puts $out "10 [eleResponse 10 localForce]"
puts $out "11 [eleResponse 11 localForce]"
puts $out "12 [eleResponse 12 localForce]"
puts $out "13 [eleResponse 13 localForce]"
puts $out "14 [eleResponse 14 localForce]"
puts $out "15 [eleResponse 15 localForce]"
puts $out "16 [eleResponse 16 localForce]"
puts $out "17 [eleResponse 17 localForce]"
puts $out "18 [eleResponse 18 localForce]"
puts $out "19 [eleResponse 19 localForce]"
puts $out "20 [eleResponse 20 localForce]"
puts $out "21 [eleResponse 21 localForce]"
puts $out "22 [eleResponse 22 localForce]"
puts $out "23 [eleResponse 23 localForce]"
puts $out "24 [eleResponse 24 localForce]"
puts $out "25 [eleResponse 25 localForce]"
puts $out "26 [eleResponse 26 localForce]"
close $out
exit 0