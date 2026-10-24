wipe
model BasicBuilder -ndm 3 -ndf 6
node 1 0 0 0
fix 1 1 1 1 1 1 1
node 2 3000 0 0
geomTransf Linear 1 0 0 1
element elasticBeamColumn 1 1 2 20000 200000 80000 100000000 80000000 40000000 1
timeSeries Linear 1
pattern Plain 1 1 {
load 2 1000 2000 3000 400000 500000 600000
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
close $out
set out [open reactions.tsv w]
puts $out "1 [nodeReaction 1]"
puts $out "2 [nodeReaction 2]"
close $out
set out [open forces.tsv w]
puts $out "1 [eleResponse 1 localForce]"
close $out
exit 0