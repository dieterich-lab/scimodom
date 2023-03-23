// -*- mode: js2; js2-additional-externs: '("$" "ko" "setTimeout") -*-
/*global ko*/
var DorinaHubId = 39859;

function bootstrap_alert(message) {
    $('#alert_placeholder').html(
        '<div class="alert alert-danger alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
        '&times;</button><span>' + message + '</span></div>')
}

function DoRiNAResult(line) {
    var self = this;
    self.cols = line.split('\t');
    self.error_state = ko.observable(false);

    self.annotations = ko.computed(function () {
        return (self.cols.length > 12) ? self.cols[12] : 'unknown#unknown*unknown';
    }, self);

    self.ann_regex = /(.*)#(.*)\*(.*)/;

    self.track = ko.computed(function () {
        var match = self.annotations().match(self.ann_regex);

        if (self.error_state()) {
            return '';
        }

        if (match) {
            return match[2];
        }

        if (self.annotations().indexOf('|') > -1) {
            match = self.annotations().split('|');
            return match[0];
        }

        var track = self.annotations();
        if (track == '') {
            track = 'unknown';
        }
        return track;
    }, self);

    self.data_source = ko.computed(function () {
        var match = self.annotations().match(self.ann_regex);
        if (self.error_state()) {
            return '';
        }

        if (match) {
            return match[1];
        }

        if (self.annotations().indexOf('|') > -1) {
            match = self.annotations().split('|');
            return match[1];
        }

        return 'CUSTOM';
    }, self);

    self.site = ko.computed(function () {
        var match = self.annotations().match(self.ann_regex);
        if (self.error_state()) {
            return '';
        }

        if (match) {
            return match[3];
        }

        if (self.annotations().indexOf('|') > -1) {
            match = self.annotations().split('|');
            return match[0];
        }

        var site = self.annotations();
        if (site == '') {
            site = 'unknown';
        }
        return site;
    }, self);

    self.gene = ko.computed(function () {
        if (self.cols.length < 9) {
            return 'unknown';
        }
        var keyvals = self.cols[8];
        var match = keyvals.match(/ID=(.*?)($|;\w+.*?=.*)/);
        if (match) {
            return match[1];
        }

        if (keyvals == '') {
            return 'unknown';
        }

        self.error_state(true);
        return keyvals;
    }, self);

    self.score = ko.computed(function () {
        if (self.error_state()) {
            return '';
        }
        return (self.cols.length > 13) ? self.cols[13] : '-1';
    }, self);

    self.location = ko.computed(function () {
        if (self.error_state()) {
            return '';
        }
        if (self.cols.length < 5) {
            return 'unknown:0-0';
        }


        return self.cols[0] + ':' + self.cols[3] + '-' + self.cols[4] +
            "(" + self.cols[6] + ")";
    }, self);

    self.feature_location = ko.computed(function () {
        if (self.error_state()) {
            return '';
        }
        if (self.cols.length < 12) {
            return 'unknown:0-0';
        }
        return self.cols[9] + ':' + self.cols[10] + '-' + self.cols[11] + "(" +
            self.cols[14] + ")";
    }, self);

}

function DoRiNAViewModel(net, uuid, custom_regulator) {
    var self = this;
    self.mode = ko.observable("choose_db");
    self.retry_after = 10000;
    self.loading_regulators = ko.observable(false);
    self.uuid = ko.observable(uuid);
    self.custom_regulator = ko.observable(custom_regulator);


    self.galaxy_url = ko.computed(function () {
        var qstring = window.location.search,
            i, l, temp, params = {}, queries;

        if (qstring.length) {
            queries = qstring.split("?")[1].split("&");
            // Convert the array of strings into an object
            for (i = 0, l = queries.length; i < l; i++) {
                temp = queries[i].split('=');
                params[temp[0]] = temp[1];
            }
            return params['GALAXY_URL'];
        } else {
            return null;
        }
    }, self);
    self.origin = ko.observable(window.location.origin);
    self.chosenAssembly = ko.observable();
    self.regulators = ko.observableArray([]);
//     self.methods = ko.observableArray([]);
    self.regulator_types = ko.observableArray([]);
    self.selected_regulators = ko.observableArray([]);
    self.selected_regulators_setb = ko.observableArray([]);
    self.results = ko.observableArray([]);
    self.total_results = ko.observable(0);
    self.offset = ko.observable(0);
    self.pending = ko.observable(false);
    self.genes = ko.observableArray([]);
    self.tissue = ko.observableArray([]);
    self.available_tissues = ko.observable(false);
    self.available_modifications = ko.observable(false);
    self.match_a = ko.observable('any');
    self.region_a = ko.observable('any');
    self.match_b = ko.observable('any');
    self.region_b = ko.observable('any');
    self.use_window_a = ko.observable(false);
    self.window_a = ko.observable(0);
    self.use_window_b = ko.observable(false);
    self.window_b = ko.observable(0);


    // Generate URL parametres for the UCSC URL to make selected supertracks
    // and subtracks visible.
    self.trackVisibility = ko.computed(function () {
        /* A supertrack is identified by the "experiment" field in the regulator
         * structure.  A subtrack is identified by the basename of the
         * associated metadata file stored in the "file" field.
         */
        if (self.selected_regulators().length > 0) {
            // selected_regulators only contains the ids but we need the full
            // objects.
            var regs = self.selected_regulators().reduce(function (acc, reg) {
                var full = self.regulators().find(function (obj) {
                    return obj.id === reg;
                });
                return full ? acc.concat([full]) : acc;
            }, []);

            var supertracks = regs.reduce(function (acc, reg) {
                if (acc.indexOf(reg.experiment) === -1) {
                    return acc.concat([reg.experiment]);
                } else {
                    return acc;
                }
            }, []).map(function (name) {
                // Remove invalid characters.  I don't know why they didn't use just
                // one replacement character for invalid characters...
                return name.replace(/\s/g, '-').replace(/:/g, '_');
            });

            var trackNamePattern = /([^\/]+)\.json/;
            var subtracks = regs.reduce(function (acc, reg) {
                var trackName = reg.file.match(trackNamePattern)[1];
                return acc.concat([trackName]);
            }, []);

            var hubPrefix = "hub_" + DorinaHubId + "_";
            var result = "&" +
                supertracks.map(function (name) {
                    return hubPrefix + name + "=show";
                }).join("&") + "&" +
                subtracks.map(function (name) {
                    return hubPrefix + name + "=dense";
                }).join("&");
            return result;
        } else {
            return "";
        }
    }, self);

    self.ucsc_url = ko.computed(function () {
        var url = "https://genome.dieterichlab.org/cgi-bin/hgTracks?db=" +
            self.chosenAssembly();
        url += "&hubUrl=https://trackhub.dieterichlab.org/eboileau/scimodomHub/hub.txt";
        url += self.trackVisibility();
        url += "&position=";
        return url;
    }, self);

    self.combinatorialOperation = ko.observable('or');

    self.readableSetOperation = ko.computed(function () {
        switch (self.combinatorialOperation()) {
            case 'or':
                return "found in set A or set B";
            case 'and':
                return "found in set A and set B";
            case 'xor':
                return "found either in set A or in set B, but not in both";
            case 'not':
                return "found in set A but not in set B";
        }
    }, self);

    self.combinatorialOpImagePath = ko.computed(function () {
        return "/static/images/" + self.combinatorialOperation() + ".svg";
    }, self);

    self.get_regulators = function (assembly) {
        var search_path = "api/v1.0/regulators/" + assembly;
        return net.getJSON(search_path).then(function (data) {
            if ('message' in data) {
                bootstrap_alert(data.message);
            }
            self.regulators.removeAll();
            self.regulator_types.removeAll();
            var regulator_types = {};

            if (self.custom_regulator()) {
                self.regulators.push({
                    id: self.uuid(),
                    experiment: 'CUSTOM',
                    summary: 'Uploaded modification data',
                    description: 'Custom modification data uploaded by user'
                });
                regulator_types['CUSTOM'] = true;
            }
            for (var i in data) {
                regulator_types[data[i].experiment] = true;
                self.regulators.push(data[i]);
            }
            for (var e in regulator_types) {
                self.regulator_types.push({id: e});
            }
        });
    };
    
//                         hard coded options
//                         ad hoc filtering 
    self.show_simple_search = function () {
        self.loading_regulators(true);
        setTimeout(function () {
                self.get_regulators(self.chosenAssembly()).then(function () {
                        
                        var options_hg38 = [{"id": "m6A GLORI"}, {"id": "m6A MazF-FTO"}, {"id": "m6A MeRIP-seq"},
                                {"id": "m6A Nanopore"}, {"id": "m6A eTAM-seq"}, {"id": "m6A m6A-SAC-seq"},
                                {"id": "m6A m6ACE-seq"}, {"id": "m6A miCLIP"}, {"id": "Y BID-seq"}, {"id": "m6A miCLIP2"}
                            ];
                        var options_hg19 = [{"id": "m6A DART-seq"}];
                        var options_mm10 = [{"id": "m6A GLORI"}, {"id": "m6A eTAM-seq"}, {"id": "Y BID-seq"}, {"id": "m6A miCLIP2"}];
                        var options_dm6 = [{"id": "m6A miCLIP"}];
//                         var options_assembly = (self.chosenAssembly() == "hg38")? options_hg38 : options_mm10;
                        
                        if (self.chosenAssembly() == "dm6") {
                            var options_assembly = options_dm6
                        } else if (self.chosenAssembly() == "mm10") {
                            var options_assembly = options_mm10
                        } else if (self.chosenAssembly() == "hg19") {
                            var options_assembly = options_hg19
                        } else {
                            var options_assembly = options_hg38
                        }

                        $('#search').collapse('show');
                        $(document.getElementById('collapseTwo')).collapse('show');
                        self.mode('search');

                        var $genes;
                        var $regulators;
                        var $regulators_setb;
                        var $shown_mods;
                        var $shown_mods_setb;
                        
                        $shown_mods = $('#shown-mods').selectize({
                            options: options_assembly,
                            items: [],
                            plugins: {
                                "remove_button": {title: "Remove"}
                            },
                            valueField: "id",
                            labelField: "id",
                            create: false,
                            onChange: function (values) {
                                regulators.disable();
                                regulators.clearOptions();
                                if (values && values.length > 0) {
                                    var filtered_regs = self.regulators().filter(function (reg) {
                                        if (reg.hasOwnProperty('tags')) {
                                            for (i in values) {
                                                const mm = values[i].split(" ");
                                                if (reg.tags.includes(mm[0])) {
                                                    if (reg.methods.includes(mm[1])) {
                                                        return reg.experiment;
                                                    }
                                                        
                                                }
                                            }
                                            
                                        }
                                    });
                                    for (var i in filtered_regs) {
                                        regulators.addOption(filtered_regs[i]);
                                    }
                                }
                                regulators.refreshOptions();
                                regulators.enable();
                            }
                        });
                        shown_mods = $shown_mods[0].selectize;
                        
                        $genes = $('#genes').selectize({
                            options: [],
                            valueField: 'id',
                            labelField: 'id',
                            searchField: 'id',
                            create: false,
                            delimiter: ' ',
                            load: function (query, callback) {
                                if (query.length == 0) {
                                    return callback();
                                }
                                net.getJSON('api/v1.0/genes/' + self.chosenAssembly() + '/' + query).then(function (res) {
                                    callback(res.genes.map(function (r) {
                                        return {id: r};
                                    }));
                                });
                            }
                        });

                        $('#tissue').change(function () {
                            if (this.value != 'none') {
                                $genes[0].selectize.disable();
                                let genesURL = tissueURL + '/' + this.value;
                                net.getJSON(genesURL, function (data) {
                                    self.genes(data.genes);
                                });
                                regulators.disable();
                                regulators.clearOptions();
                                var filtered_regs = self.regulators(
                                ).filter(function (reg) {
                                    // extract regulator for regulators obj
                                    // check if it is the loaded genes
                                    // filter searcheable regulators
                                    return self.genes().indexOf(
                                        reg.summary.split(' ')[0]) > -1;
                                });
                                for (var i in filtered_regs) {
                                    regulators.addOption(filtered_regs[i]);
                                };
                                regulators.refreshOptions();
                                regulators.enable();
                            }
                            else {
                                for (var i in self.regulators()) {
                                    regulators.addOption(self.regulators()[i]);
                                };
                                regulators.refreshOptions();
                                regulators.enable();Í
                                $genes[0].selectize.enable();
                            }
                        });

//                         $shown_types_setb = $('#shown-types-setb').selectize({
//                             options: self.regulator_types(),
//                             items: [],
//                             valueField: 'id',
//                             labelField: 'id',
//                             onChange: function (values) {
//                                 regulators_setb.disable();
//                                 if (values && values.length > 0) {
//                                     var filtered_regs = self.regulators().filter(function (reg) {
//                                         return values.indexOf(reg.experiment) > -1;
//                                     });
// 
//                                     for (var i in filtered_regs) {
//                                         regulators_setb.addOption(filtered_regs[i]);
//                                     }
//                                 }
// 
//                                 regulators_setb.refreshOptions();
//                                 regulators_setb.enable();
//                             }
//                         });
//                         shown_types_setb = $shown_types_setb[0].selectize;
                        
                        $shown_mods_setb = $('#shown-mods-setb').selectize({
                            options: options_assembly,
                            items: [],
                            plugins: {
                                "remove_button": {title: "Remove"}
                            },
                            valueField: "id",
                            labelField: "id",
                            create: false,
                            onChange: function (values) {
                                regulators_setb.disable();
                                regulators_setb.clearOptions();
                                if (values && values.length > 0) {
                                    var filtered_regs = self.regulators().filter(function (reg) {
                                        if (reg.hasOwnProperty('tags')) {
                                            for (i in values) {
                                                const mm = values[i].split(" ");
                                                if (reg.tags.includes(mm[0])) {
                                                    if (reg.methods.includes(mm[1])) {
                                                        return reg.experiment;
                                                    }
                                                        
                                                }
                                            }
                                            
                                        }
                                    });
                                    for (var i in filtered_regs) {
                                        regulators_setb.addOption(filtered_regs[i]);
                                    }
                                }
                                regulators_setb.refreshOptions();
                                regulators_setb.enable();
                            }
                        });
                        shown_mods_setb = $shown_mods_setb[0].selectize;

                        $regulators = $('#regulators').selectize({
                            options: self.regulators(),
                            create: false,
                            valueField: 'id',
                            labelField: 'summary',
                            searchField: 'summary',
                            optgroups: self.regulator_types(),
                            optgroupField: 'experiment',
                            optgroupValueField: 'id',
                            optgroupLabelField: 'id',
                            render: {
                                option: function (item, escape) {
                                    return '<div><span class="regulator">' + escape(item.summary) +
                                        '</span><br><span class="description">' + escape(item.description) + '</span></div>';
                                }
                            }
                        });
                        regulators = $regulators[0].selectize;

                        $regulators_setb = $('#regulators_setb').selectize({
                            options: self.regulators(),
                            create: false,
                            valueField: 'id',
                            labelField: 'summary',
                            searchField: 'summary',
                            optgroups: self.regulator_types(),
                            optgroupField: 'experiment',
                            optgroupValueField: 'id',
                            optgroupLabelField: 'id',
                            render: {
                                option: function (item, escape) {
                                    return '<div><span class="regulator">' + escape(item.summary) +
//                                         '</span><br><span class="description">(' + escape(item.sites) + ' sites) '
                                        + escape(item.description) + '</span></div>';
                                }
                            }
                        });
                        regulators_setb = $regulators_setb[0].selectize;
                        if (self.custom_regulator()) {
                            regulators.addItem(self.uuid());
                        }

                        self.loading_regulators(false);
                    }
                );
            },
            10
        );
    }
    ;

    self.run_search = function (keep_data) {
        var search_data = {

            set_a: self.selected_regulators(),
            assembly: self.chosenAssembly(),
            match_a: self.match_a(),
            region_a: self.region_a(),
            genes: self.genes(),
            offset: self.offset(),
            uuid: self.uuid(),
            tissue: self.tissue()
        };

        if (self.use_window_a()) {
            search_data.window_a = self.window_a();
        }
        // if there's any selection made for set B regulators,
        // send set B data
        if (self.selected_regulators_setb().length > 0) {
            search_data.set_b = self.selected_regulators_setb();
            search_data.match_b = self.match_b();
            search_data.region_b = self.region_b();
            search_data.combinatorial_op = self.combinatorialOperation();
            if (self.use_window_b()) {
                search_data.window_b = self.window_b();
            }
        }
        self.pending(true);

        if (!keep_data) {
            self.results.removeAll();
        }

        return net.post('api/v1.0/search', search_data).then(function (data) {
            if ('message' in data) {
                bootstrap_alert(data.message);
            }
            self.uuid(data.uuid);
            self.poll_result(data.uuid);
        });
    };

    self.poll_result = function (uuid) {
        var url = 'api/v1.0/status/' + uuid;
        net.getJSON(url).then(function (data) {
            if ('message' in data) {
                bootstrap_alert(data.message);
            }
            if (data.state == 'pending') {
                setTimeout(function () {
                    self.poll_result(uuid);
                }, self.retry_after);
                return;
            }

            return self.get_results(uuid);
        });
    };

    self.get_results = function (uuid, more) {
        var url = '/api/v1.0/result/' + uuid;

        $("#collapseTwo").find("*").prop('disabled', true);

        self.table = $("#resultTable").DataTable(
            {
                ajax: {
                    "url": url,
                    "dataSrc": function (json) {
                        var temp = [];
                        for (var x in json.results) {
                            result_i = new DoRiNAResult(json.results[x]);

                            temp.push(
                                Array(
                                    //result_i.track,
                                    result_i.gene,
                                    result_i.data_source,
                                    result_i.score,
                                    result_i.site,
                                    result_i.location,
                                    result_i.feature_location));
                        }
                        if ('message' in json) {
                            bootstrap_alert(json.message);
                        }
                        return temp;
                    }
                },
                deferRender: true,
                responsive: true,
                language:
                    {
                        lengthMenu: "Display _MENU_ records per page",
                        zeroRecords: "No records available",
                        infoEmpty: "No data",
                        loadingRecords: "Loadig, please wait",
                        processing: "Processing, please wait",
                    },
                columns: [
                    {title: "Feature"},
                    {title: "Data source"},
                    {title: "Score"},
                    {title: "Modification"},
                    {title: "Feature coordinates"},
                    {title: "Modification coordinates"}],
                columnDefs: [
                    {
                        targets: [4, 5],
                        render: function (data, type, row) {
                            data = '<a target="_blank" href="' + self.ucsc_url() +
                                data().split('(')[0] + '">' + data() + '</a>';
                            return data;
                        }
                    }
                ],
                "order":
                    [[2, "desc"]]
            }
        );
        $(document.getElementById("collapseThree")).collapse("show");
        self.pending(false);
    };

    self.clear_selections = function () {
        $('#regulators')[0].selectize.clear();
        $('#regulators_setb')[0].selectize.clear();
    };

    /* These functions break the ViewModel abstraction a bit, as they trigger
     * view changes, but I can't think of a better way to implement this at the
     * moment */
    self.run_simple_search = function () {
        self.run_search(false);
        self.mode('results');
    };
}

function RegulatorViewModel(net, value) {
    var self = this;

    self.regulators = ko.observableArray([]);

    self.init = function () {
        self.get_regulators(value);
    };

    self.get_regulators = function (assembly) {

        return net.getJSON('/api/v1.0/regulators/' + assembly).then(function (data) {

            self.regulators.removeAll();
            self.regulators.extend({rateLimit: 60});
            if ('message' in data) {
                bootstrap_alert(data.message);
            }
            for (var reg in data) {
                self.regulators.push(data[reg]);
            }

            self.regulators.sort(function (a, b) {
                return (a.summary.toUpperCase() > b.summary.toUpperCase()) -
                    (b.summary.toUpperCase() > a.summary.toUpperCase());

            });
        });
    };
}

function SetViewModel(view_model) {
    $(document).data('view_model', view_model);
}

function GetViewModel() {
    return $(document).data('view_model');
}
