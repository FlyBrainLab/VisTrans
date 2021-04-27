window.sendMaster = function (x) {
    window.top.postMessage(x, '*');
}
var ommatidium_data_set = false;

/*
 * Create neuron list
 */
var svgObj = d3.select(document.querySelector('svg'));
var num_of_ommatidium = 721;
var ommaList = [];
for (var i = 0; i < 721; i++) {
    ommaList.push('ommatidium' + i);
}

var retina_data_set = false;

function toggleByID(a) {
    console.log(a)
    var neu = svgObj.select("#" + a)
    var hideOrShow = "remove";
    $("#btn-" + a).toggleClass("selected unselected");
    if (neu.attr("visible") == "true") {
        console.log(neu.attr("visible"));
        console.log(neu.style("opacity"));
        neu.attr("visible", "false");
        neu.style("opacity", "0.3");
        console.log(neu.style("opacity"));
        $("#btn-" + a).html('&EmptySmallSquare; ' + a);
        hideOrShow = "remove";
    } else {
        console.log(neu.attr("visible"));
        console.log(neu.style("opacity"));
        neu.attr("visible", "true");
        neu.style("opacity", "1.0");
        console.log(neu.style("opacity"));
        $("#btn-" + a).html('&FilledSmallSquare; ' + a)
        hideOrShow = "add";
    }

    // svgObj.selectAll("." + a + "-dependent")
    //     .style("opacity", function () {

    //         var count = parseInt((d3.select(this).attr("count")), 10);

    //         if (neu.attr("visible") == "false") {
    //             count += 1;
    //             d3.select(this).attr("count", count);
    //             return "0.0";
    //         } else {
    //             count -= 1;
    //             d3.select(this).attr("count", count);
    //             if (count == 0) {
    //                 return "1.0";
    //             } else {
    //                 return "0.0";
    //             } 
    //         }
    //     });

    if (ommatidium_data_set) {
        $("#num-of-ommatidium").text("Ommatidium #" + ommatidium_num + ", Number of Neurons: " + getNeuronCount());
    }
    id = (a.substring(1) - 5) / 6;
    //ffboMesh.toggleVis(a);
    //console.log(a);
    window._neuGFX.mods.FlyBrainLab.sendMessage({messageType:'NLPquery', query: hideOrShow + " /rR[1-8]-" + id + '/r'});
}


for (var i = 0; i < ommaList.length; i++) {
    var id = ommaList[i];
    $("#single-omma").append("<li><a id='" + "btn" + "-" + id + "' role='button' class='btn-omma-single selected'>&FilledSmallSquare; " + id + "</a></li>");
}
$(".btn-omma-single").click(function () {
    var id = $(this).attr("id").substring(4);
    toggleByID(id);
});
/*
 * create neuron 3D mesh
 */


onAddAllClick = function () {
    //ffboMesh.showAll();
    svgObj.selectAll(".ommatidium")
        .attr("visible", "true")
        .style("opacity", "1.0")
        .each(function () {})
    $(".btn-omma-single").each(function () {
        var id = $(this).attr("id").substring(4);
        $(this).removeClass("unselected");
        $(this).addClass("selected");
        $(this).html('&FilledSmallSquare; ' + id)
    });
    num_of_ommatidium = 721;
    $("#num-of-ommatidium").text("Number of Ommatidia:" + num_of_ommatidium)
}
onRemoveAllClick = function () {}
//     console.log('remove all');
//     svgObj.selectAll(".ommatidium")
//         .attr("visible", "false")
//         .style("opacity", "0.3")
//         .each(function () {})
//     $(".btn-omma-single").each(function () {
//         var id = $(this).attr("id").substring(4);
//         $(this).removeClass("selected");
//         $(this).addClass("unselected");
//         $(this).html('&EmptySmallSquare; ' + id)
//         svgObj.selectAll(".ommatidium")
//     });
//     num_of_ommatidium = 0;
//     $("#num-of-ommatidium").text("Number of Ommatidia:" + num_of_ommatidium)
//     //ffboMesh.hideAll();
// }
svgObj.selectAll(".omma")
    .style("cursor", "pointer")
    .style("opacity", "1.0")
    .attr("visible", "true")
    .each(function () {
        var a = d3.select(this).attr("id");
        //console.log(a);
        d3.select(this).selectAll(".ommatidium")
            .style("cursor", "pointer")
            .style("opacity", "1.0")
            .attr("visible", "true")
    })
    .on("click", function () {
        var id = d3.select(this).attr("id");
        //console.log(id);
        toggleByID(id);
        id = id.substring(1);
        // window._neuGFX.mods.FlyBrainLab.sendMessage({messageType:'NLPquery', query: hideOrShow + " /rR[1-8]-" + id + '/r'});
        // id = 'circle' + (id - 5) / 6;

    })
    .on("dblclick", function () {
        var id = d3.select(this).attr("id");
        id = (id.substring(1) - 5) / 6;
        window.customCircuitAttributes = {
            'ommatidium_num': id
        };
        console.log(window.submodules['ommatidium']);
        window._neuGFX.mods.FlyBrainLab.gfx.loadSVGFromString(
            window._neuGFX.mods.FlyBrainLab.circuitContent['ommatidium'],
            function () {
                eval(window.submodules['ommatidium']);
                console.log("Submodule loaded.")
            }
        );
        window._neuGFX.mods.FlyBrainLab.circuitName = 'ommatidium';
        // window._neuGFX.mods.FlyBrainLab.loadFBLSVG('ommatidium', function () {
        //     eval(window.submodules['ommatidium']);
        //     console.log("Submodule loaded.")
        // });
        //window._neuGFX.mods.FlyBrainLab.sendMessage({ messageType: 'NLPquery', query: "show neurons in column home" }, '*');
    })




console.log('Loading was successful...');
window._neuGFX.mods.FlyBrainLab.addFBLPath("Retina", function () {
    window._neuGFX.mods.FlyBrainLab.gfx.loadSVGFromString(
        window._neuGFX.mods.FlyBrainLab.circuitContent['retina'],
        function () {
            eval(window.submodules['retina']);
            console.log("Submodule retina loaded.")
        })
    // eval(window.submodules['retina']);
    // console.log("Submodule loaded.");
});