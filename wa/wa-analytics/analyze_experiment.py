# -*- coding: utf-8 -*-

# Copyright 2015 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Thiago Salles [tsalles@br.ibm.com]

import json
import argparse
import csv
import os.path

def median(data=None, sorted_data=None):
    if not data and not sorted_data: return 0
    if not sorted_data: sorted_data = sorted(data)
    mid = len(sorted_data) // 2
    return (sorted_data[mid-1] + sorted_data[mid]) / 2.0 if (len(sorted_data) % 2 == 0) else sorted_data[mid]


def quartiles(data):
    if not data: return (0,0)
    sorted_data = sorted(data)
    mid = len(sorted_data) // 2
    return (median(sorted_data=sorted_data[:mid]),
            median(sorted_data=sorted_data),
            median(sorted_data=sorted_data[mid:]) if  (len(sorted_data) % 2 == 0) else median(sorted_data=sorted_data[mid+1:]))


def parse(input_dir):
    results = []
    k = 0
    while os.path.isfile('{}/test_{}.csv'.format(input_dir, k)) and os.path.isfile('{}/predictions_{}.txt'.format(input_dir, k)): k+= 1

    for i in range(k):
        with open('{}/test_{}.csv'.format(input_dir, i), encoding="UTF-8") as test_file, open('{}/predictions_{}.txt'.format(input_dir, i), encoding="UTF-8") as pred_file:
            test_r, pred_r = csv.reader(test_file, delimiter=','), csv.reader(pred_file, delimiter=' ')
            for test_row in test_r:
                pred_row = next(pred_r)
                if len(test_row) > 1 and len(pred_row) > 1:
                     results.append((test_row[0], test_row[1], [(x.split(':')[0], x.split(':')[1]) for x in pred_row[2:]]))

    prec_at_k = {}
    with open('{}/precision_at_k.txt'.format(input_dir), 'r', encoding="UTF-8") as pk_file:
        pk_reader = csv.reader(pk_file, delimiter=' ')
        for row in pk_reader:
            if len(row) > 1:
                prec_at_k[row[0]] = (float(row[1]), float(row[2]))
    return results, prec_at_k


def prec_at_k_script(prec_at_k):
    return '''
        var chart = c3.generate({{
            bindto: '#prec_at_k_plot',
            size: {{ height: 480 }},
            data: {{
                x: 'k',
                columns: [
                    ['k', {k_values}],
                    ['Accuracy', {accuracy_values}]
                ],
                type: "bar"
            }},
            axis: {{
                x: {{
                    label: {{
                        text: 'K',
                        position: 'outer-center'
                    }},
                    tick: {{
                      culling: false
                    }}
                }},
                y: {{
                    label: {{
                        text: 'Accuracy (%)',
                        position: 'outer-middle'
                    }},
                    tick: {{
                      culling: false
                    }},
                    padding: {{top:0, bottom:0}},
                    max: 100,
                    min: 0,
                }}
            }},
            legend: {{
                hide: true
            }},
            tooltip: {{
                format: {{
                    title: function (d) {{
                        return 'Precision@' + d;
                    }}
                }}
            }}
        }});
    '''.format(k_values=','.join(str(x) for x in prec_at_k.keys()), accuracy_values=','.join(str(float(x[0])*100) for x in prec_at_k.values()))


def prec_at_k_table(prec_at_k):
    rows = '\n'.join('<tr><td class="text-center">{}</td><td class="text-center">{}</td><td class="text-center">{}</td></tr>\n'.format(x[0], '{0:.2f}'.format(x[1]), '{0:.2f}'.format(x[2])) for x in sorted(((int(k), float(v[0])*100, float(v[1])*100) for k, v in prec_at_k.items())))
    return '''
      <table class="table table-striped">
        <thead>
          <tr><th rowspan=2 class="text-center">K</th><th colspan=2 class="text-center">Precision</th></tr>
          <tr><th class="text-center">Average (%)</th><th class="text-center">Std Dev (%)</th></tr>
        </thead>
        <tbody>
          {}
        </tbody>
      </table>
      '''.format(rows)


def pairwise_errors(preds):
    conf, n, err, exs = {}, {}, {}, {}
    for p in preds:
        q, real_cl, pred_cl, c = p[0], p[1], p[2][0][0], float(p[2][0][1])
        if real_cl not in exs:
            exs[real_cl] = []
        exs[real_cl].append(q)
        if real_cl != pred_cl:
            key = '{}#{}'.format(real_cl, pred_cl)
            conf[key] = conf.get(key, 0.0) + c
            n[key] = n.get(key, 0.0) + 1.0
            if key not in err: err[key] = []
            err[key].append(q)
    conf = {k : v/n[k] for k, v in conf.items()}
    data = {k : {'real': k.split('#')[0], 'pred': k.split('#')[1], 'total': int(v), 'conf': conf.get(k, 0.0), 'errors': err.get(k, [])} for k, v in n.items()}
    return sorted(data.values(), key=lambda x: (x['total'], x['conf']), reverse=True), exs


def accuracy_vs_coverage(preds):
    absent, n, hits = {}, {}, {}
    for score in [x/10 for x in range(2, 11)]:
        for p in preds:
            real_cl, pred_cl, c = p[1], p[2][0][0], float(p[2][0][1])
            if c < score:
                absent[score] = absent.get(score, 0) + 1
            else:
                n[score] = n.get(score, 0) + 1
                if pred_cl == real_cl:
                    hits[score] = hits.get(score, 0) + 1
    result = {}
    for score in [x/10 for x in range(2, 11)]:
        total = (absent.get(score, 0) + n.get(score, 0))
        coverage = 1 - ((absent.get(score, 0) / total) if total else 0)
        accuracy = hits.get(score, 0) / n[score] if score in n else 0
        result[score] = {'coverage': coverage, 'accuracy': accuracy}
    return result


def accuracy_vs_coverage_script(data):
    cov_map = {"{0:.2f}".format(data[x]['coverage']*100) : "{0:.2f}".format(x*100) for x in sorted(data.keys())}
    return '''
        var cov_map = {cov_map};
        c3.generate({{
            bindto: '#accuracy_coverage_plot',
            size: {{ height: 480 }},
            data: {{
                x: 'scores',
                columns: [
                    ['scores', {scores}],
                    ['accuracy', {accuracy}],
                    ['coverage', {coverage}]
                ],
                axes: {{
                    coverage: 'y2'
                }},
                names: {{
                    accuracy: 'Accuracy',
                    coverage: 'Coverage',
                    scores: 'Confidence'
                }},
                //type: "scatter",
            }},
            point: {{ r: 5 }},
            axis: {{
                x: {{
                    tick: {{
                        format: function (x) {{ return x; }},
                        multiline: false
                    }},
                    label: {{
                        text: 'Confidence',
                        position: 'outer-center'
                    }},
                }},
                y: {{
                    label: {{
                        text: 'Accuracy (%)',
                        position: 'outer-middle'
                    }},
                    padding: {{top:0, bottom:0}},
                    max: 100,
                    min: 0,
                }},
                y2: {{
                    show: true,
                    label: {{
                        text: 'Coverage (%)',
                        position: 'outer-middle'
                    }},
                    padding: {{top:0, bottom:0}},
                    max: 100,
                    min: 0,
                }},
            }},
            tooltip: {{
                format: {{
                    title: function (d) {{
                        return 'Confidence ' + d;
                    }}
                }},
            }}
        }});
    '''.format(scores=','.join("{0:.2f}".format(x*100) for x in sorted(data.keys())), cov_map=cov_map,
               coverage=','.join("{0:.2f}".format(data[x]['coverage']*100) for x in sorted(data.keys())),
               accuracy=','.join("{0:.2f}".format(data[x]['accuracy']*100) for x in sorted(data.keys())))


def class_stats(preds):
    stats = {}
    for p in preds:
        real_cl, pred_cl = p[1], p[2][0][0]
        if real_cl not in stats: stats[real_cl] = {'real': real_cl, 'total': 0, 'hits': 0}
        stats[real_cl]['total'] += 1
        stats[real_cl]['hits'] += 1 if real_cl == pred_cl else 0
    result = {k: {'real': k, 'total': v['total'], 'hits': v['hits'], 'accuracy': float(v['hits'])/float(v['total'])} for k, v in stats.items()}
    return sorted(result.values(), key=lambda x: (x['total'], x['accuracy']), reverse=True)


def class_accuracy_table(dataset):
    sz_lower_q, sz_median, sz_upper_q = quartiles(x['total'] for x in dataset)
    acc_lower_q, acc_median, acc_upper_q = quartiles(x['accuracy'] for x in dataset)
    total = sum(x['total'] for x in dataset)
    rows = '\n'.join('<tr{style}><td>{real}</td><td>{total}</td><td>{accuracy}</td></tr>'.format(
        style=' class="danger"' if x['total'] > sz_upper_q and x['accuracy'] < acc_lower_q else ' class="warning"' if x['accuracy'] < acc_median else ' ',
        real=x['real'],
        total=x['total'],
        accuracy='{0:.2f}'.format(x['accuracy']*100)) for x in dataset)
    return '''
      <table class="table table-striped">
        <thead>
          <tr><th>Class Name</th><th>Class Size</th><th>Accuracy (%)</th></tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
        <tfoot>
          <tr><td><b>Total</b></td><td><b>{total} ({classes} intents)</b></td><td><b>{avg_acc}</b></td></tr>
        </tfoot>
      </table>
      '''.format(rows=rows, total=total, classes=len([x['real'] for x in dataset]), avg_acc='{0:.2f}'.format((sum(float(x['hits']) for x in dataset)/total)*100))


def class_accuracy_script(dataset):
    sz_lower_q, sz_median, sz_upper_q = quartiles(x['total'] for x in dataset)
    acc_lower_q, acc_median, acc_upper_q = quartiles(x['accuracy'] for x in dataset)

    danger, warning, info = [], [], []
    for x in dataset:
        if x['total'] > sz_upper_q and x['accuracy'] < acc_lower_q:
            danger.append((x['total'], x['accuracy']))
        elif x['accuracy'] < acc_median:
            warning.append((x['total'], x['accuracy']))
        else:
            info.append((x['total'], x['accuracy']))
    return '''
       c3.generate({{
           bindto: '#class_accuracy_pie',
           size: {{ height: 300 }},
           data: {{
               columns: [
                 ['Danger', {num_danger}],
                 ['Warning', {num_warning}],
                 ['Good', {num_info}]
               ],
               type : 'pie',
               colors: {{
                  Danger: '#e86f6f',
                  Warning: '#e0c741',
                  Good: '#1f77b4'
               }},
           }},
           pie: {{
               label: {{
                   show: true,
                   format: function (value, ratio, id) {{
                       return value + ' (' + d3.format('%')(ratio) + ')';
                   }}
               }},
               expand: true,
           }},
           tooltip: {{
               format: {{
                   value: function(value, ratio) {{
                       return value + ' (' + d3.format('%')(ratio) + ')';
                   }}
               }}
           }},
           donut: {{
               title: "Accuracy vs Size"
           }}
        }});

        c3.generate({{
            bindto: '#class_accuracy_plot',
            size: {{ height: 480 }},
            data: {{
                xs: {{
                  danger_acc: 'danger_sz',
                  warning_acc: 'warning_sz',
                  info_acc: 'info_sz'
                }},
                columns: [
                    ['danger_sz', {danger_sz}],
                    ['warning_sz', {warning_sz}],
                    ['info_sz', {info_sz}],
                    ['danger_acc', {danger_acc}],
                    ['warning_acc', {warning_acc}],
                    ['info_acc', {info_acc}],
                ],
                names: {{
                    danger_acc: 'Danger',
                    warning_acc: 'Warning',
                    info_acc: 'Good'
                }},
                colors: {{
                  danger_acc: '#e86f6f',
                  warning_acc: '#e0c741',
                  info_acc: '#1f77b4'
                }},
                type: "scatter",
            }},
            point: {{ r: 5 }},
            axis: {{
                x: {{
                    tick: {{
                        format: function (x) {{ return x; }},
                        multiline: false
                    }},
                    label: {{
                        text: 'Class Size',
                        position: 'outer-center'
                    }},
                }},
                y: {{
                    label: {{
                        text: 'Mean Accuracy (%)',
                        position: 'outer-middle'
                    }},
                    padding: {{top:0, bottom:0}},
                    max: 100,
                    min: 0,
                }},
            }},
            legend: {{
                hide: false
            }},
            tooltip: {{
                format: {{
                    title: function (d) {{
                        return 'Class ' + cl_map[d];
                    }}
                }},
            }}
        }});
    '''.format(danger_acc=','.join(str(x[1]*100) for x in danger), danger_sz=','.join(str(x[0]) for x in danger), num_danger=len(danger),
               warning_acc=','.join(str(x[1]*100) for x in warning), warning_sz=','.join(str(x[0]) for x in warning), num_warning=len(warning),
               info_acc=','.join(str(x[1]*100) for x in info), info_sz=','.join(str(x[0]) for x in info), num_info=len(info))

def class_distribution_table(dataset):
    lower_q, median, upper_q = quartiles(x['total'] for x in dataset)
    total = sum(x['total'] for x in dataset)
    rows = '\n'.join('<tr{style}><td>{real}</td><td>{total}</td></tr>'.format(
        style=' class="danger"' if x['total'] < lower_q else ' class="warning"' if x['total'] < upper_q else '',
        real=x['real'],
        total=x['total']) for x in dataset)
    return '''
      <table class="table table-striped">
        <thead>
          <tr><th>Class Name</th><th>Class Size</th></tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
        <tfoot>
          <tr><td><b>Total</b></td><td><b>{total} examples into {classes} intents.</b></td></tr>
        </tfoot>
      </table>
      '''.format(rows=rows, total=total, classes=len([x['real'] for x in dataset]))


def class_distribution_script(dataset):
    lower_q, median, upper_q = quartiles(x['total'] for x in dataset)
    num_danger, num_warning, num_info = 0, 0, 0
    for x in dataset:
        if x['total'] < lower_q:
            num_danger += 1
        elif x['total'] < upper_q:
            num_warning += 1
        else:
            num_info += 1
    return '''
        var cl_map = [{class_names}];
        c3.generate({{
           bindto: '#class_distribution_pie',
           size: {{ height: 300 }},
           data: {{
               columns: [
                 ['Danger', {num_danger}],
                 ['Warning', {num_warning}],
                 ['Good', {num_info}]
               ],
               type : 'pie',
               colors: {{
                  Danger: '#e86f6f',
                  Warning: '#e0c741',
                  Good: '#1f77b4'
               }},
           }},
           pie: {{
               label: {{
                   show: true,
                   format: function (value, ratio, id) {{
                       return value + ' (' + d3.format('%')(ratio) + ')';
                   }},
               }},
               expand: true,
           }},
           tooltip: {{
               format: {{
                   value: function(value, ratio) {{
                       return value + ' (' + d3.format('%')(ratio) + ')';
                   }}
               }}
           }},
           donut: {{
               title: "Accuracy vs Size"
           }}
        }});
        c3.generate({{
                 bindto: '#class_distribution_plot',
                 size: {{ height: 480 }},
                 data: {{
                     columns: [
                         ['Class Size', {class_sizes}]
                     ],
                     type: "bar",
                     color: function (color, d) {{
                         if (d.id) {{ // && d.id === 'Class Size') {{
                           if (d.value < {lower_q}) return '#e86f6f';
                           else if (d.value < {upper_q}) return '#e0c741';
                           return color;
                         }}
                         return color;
                     }},
                 }},
                 axis: {{
                     x: {{
                         type: 'category',
                         categories: [{class_names}],
                         tick: {{
                             format: function (x) {{ return cl_map[x]; }},
                             rotate: 90,
                             multiline: false
                         }},
                         height: 200,
                         label: {{
                           text: 'Class',
                           position: 'outer-center'
                         }}
                     }},
                     y: {{
                         show: true,
                         label: {{
                             text: 'Number of Examples',
                             position: 'outer-middle'
                         }},
                     }},
                 }},
                 grid: {{
                   y: {{
                        lines: [
                          {{value: {lower_q}, text: 'Lower Quartile'}},
                          {{value: {median}, text: 'Median'}},
                          {{value: {upper_q}, text: 'Upper Quartile'}}
                        ]
                    }}
                 }},
                 zoom: {{
                     enabled: true
                 }},
                 legend: {{
                     hide: true
                 }},
                 tooltip: {{
                     format: {{
                         title: function (d) {{
                             return 'Class ' + cl_map[d];
                         }}
                     }},
                     contents: function (d, defaultTitleFormat, defaultValueFormat, color) {{
                         color = function() {{
                             if (d[0].value < {lower_q}) return '#e86f6f';
                             else if (d[0].value < {upper_q}) return '#e0c741';
                             else return '#1f77b4';
                         }};
                         return chart.internal.getTooltipContent.call(this, d, defaultTitleFormat, defaultValueFormat, color)
                     }}

                 }}
             }});
        '''.format(class_names=','.join("'{}'".format(x['real']) for x in dataset), class_sizes=','.join(str(x['total']) for x in dataset),
                   lower_q=lower_q, upper_q=upper_q, median=median, num_danger=num_danger, num_warning=num_warning, num_info=num_info)


def pairwise_script(pairwise_err):
    num_danger, num_warning, num_info = 0, 0, 0
    for x in pairwise_err:
        if x['conf'] > 0.8:
            num_danger += 1
        elif x['conf'] < 0.5:
            num_warning += 1
        else:
            num_info += 1
    return '''
        c3.generate({{
           bindto: '#pairwise_pie',
           size: {{ height: 300 }},
           data: {{
               columns: [
                 ['Danger', {num_danger}],
                 ['Warning', {num_warning}],
                 ['Good', {num_info}]
               ],
               type : 'pie',
               colors: {{
                  Danger: '#e86f6f',
                  Warning: '#e0c741',
                  Good: '#1f77b4'
               }},
           }},
           pie: {{
               label: {{
                   show: true,
                   format: function (value, ratio, id) {{
                       return value + ' (' + d3.format('%')(ratio) + ')';
                   }}
               }},
               expand: true,
           }},
           tooltip: {{
               format: {{
                   value: function(value, ratio) {{
                       return value + ' (' + d3.format('%')(ratio) + ')';
                   }}
               }}
           }},
           donut: {{
               title: "Pairwise Class Error"
           }}
        }});
        '''.format(num_danger=num_danger, num_warning=num_warning, num_info=num_info)

def pairwise_examples(pairwise_err, examples):
    data, classes = [], set()
    for x in pairwise_err:
        data.append('''
            <div class="modal fade" id="errors-{real}-{pred}" role="dialog">
              <div class="modal-dialog modal-lg">
                <div class="modal-content">
                  <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal">&times;</button>
                    <h4 class="modal-title">Should be #{real} but was #{pred}</h4>
                  </div>
                  <div class="modal-body">
                    {examples}
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                  </div>
                </div>
              </div>
            </div>
        '''.format(real=x['real'], pred=x['pred'], examples='\n'.join('<p>{}</p>'.format(e) for e in x['errors']) if x['errors'] else 'No errors!'))
        target_cls = []
        if x['real'] not in classes:
            target_cls.append(x['real'])
            classes.add(x['real'])
        if x['pred'] not in classes:
            target_cls.append(x['pred'])
            classes.add(x['pred'])
        for tgt_cl in target_cls:
            data.append('''
                <div class="modal fade" id="examples-{real}" role="dialog">
                  <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                      <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                        <h4 class="modal-title">#{real} examples</h4>
                      </div>
                      <div class="modal-body">
                        {examples}
                      </div>
                      <div class="modal-footer">
                        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                      </div>
                    </div>
                  </div>
                </div>
            '''.format(real=tgt_cl, examples='\n'.join('<p>{}</p>'.format(e) for e in examples[tgt_cl])))
    return '\n'.join(data)


def pairwise_table(pairwise_err):
    rows = '\n'.join('<tr{style}><td class="text-center"><a data-target="#examples-{real}" data-toggle="modal">{real}</a></td><td class="text-center"><a data-target="#examples-{pred}" data-toggle="modal">{pred}</a></td><td class="text-center"><a data-target="#errors-{real}-{pred}" data-toggle="modal">{total}</a></td><td class="text-center">{conf}</td></tr>'.format(
        style=' class="danger"' if x['conf']>0.8 else ' class="warning"' if x['conf']>0.5 else '',
        real=x['real'], pred=x['pred'], total=x['total'], conf='{0:.2f}'.format(x['conf']*100)) for x in pairwise_err)
    return '''
       <table class="table table-striped">
        <thead>
          <tr>
            <th class="text-center">Real</th>
            <th class="text-center">Predicted</th>
            <th class="text-center">Errors</th>
            <th class="text-center">Avg Confidence (%)</th>
          </tr>
        </thead>
        <tbody>
          {}
        </tbody>
      </table>
    '''.format(rows)


def pairwise_graph_script(pairwise_err):
    data = 'var links = [\n';
    data += '\n  '.join('{{real: "{}", pred: "{}", errors: {}, avg_conf: {}}},'.format(x['real'], x['pred'], x['total'], x['conf']) for x in pairwise_err if x['total']>0)
    data += '\n];'
    max_err = max([x['total'] for x in pairwise_err if x['total'] > 0])
    return '''
      function pageHeight() {{
        var lReturn = window.innerHeight;
        if (typeof lReturn == "undefined") {{
            if (typeof document.documentElement != "undefined" && typeof document.documentElement.clientHeight != "undefined") {{
                lReturn = document.documentElement.clientHeight;
            }} else if (typeof document.body != "undefined") {{
                lReturn = document.body.clientHeight;
            }}
        }}
        return lReturn;
      }}

      // method to get page width
      function pageWidth() {{
          var lReturn = window.innerWidth;
          if (typeof lReturn == "undefined") {{
              if (typeof document.documentElement != "undefined" && typeof document.documentElement.clientWidth != "undefined") {{
                  lReturn = document.documentElement.clientWidth;
              }} else if (typeof document.body != "undefined") {{
                  lReturn = document.body.clientWidth;
              }}
          }}
          return lReturn;
      }}

      $(function () {{
          {data}

          var danger = true, warning = true, good = true;
          var nodes = {{}};

          // Compute the distinct nodes from the links.
          links.forEach(function (link) {{
              link.value = link.errors;
              link.type = link.avg_conf > 0.8 ? 'Danger' : (link.avg_conf > 0.5 ? 'Warning' : 'Good');
              link.stroke = link.avg_conf > 0.8 ? '#e86f6f' : (link.avg_conf > 0.5 ? '#e0c741' : '#1f77b4');
              link.source = nodes[link.real] || (nodes[link.real] = {{
                  name: link.real,
                  value: link.errors
              }});
              link.target = nodes[link.pred] || (nodes[link.pred] = {{
                  name: link.pred,
                  value: link.errors
              }});
          }});

          links.forEach(function(link) {{
            if (typeof link.real === 'undefined') {{
                console.log('undefined real', link);
            }}
            if (typeof link.target === 'undefined') {{
                console.log('undefined target', link);
            }}
          }});

          function brushed() {{
            var value = brush.extent()[0];

            if (d3.event.sourceEvent) {{
              value = x.invert(d3.mouse(this)[1]);
              brush.extent([value, value]);
            }}
            handle.attr("cy", x(value));
            var threshold = value;

            filterGraph(threshold);
          }}

          var w = pageWidth()/2,
              h = pageHeight() - 200;

          var force = d3.layout.force()
                        .nodes(d3.values(nodes))
                        .links(links)
                        .size([w, h])
                        .linkDistance(60)
                        //.linkStrength(function(d) {{ return (d.value/{max_err} - 0.01)/1000 }})
                        .charge(-300)
                        .on("tick", tick)
                        .start();

          var svg = d3.select(".graphContainer")
                      .append("svg:svg")
                      .attr("width", w)
                      .attr("height", h);

          function zoomHandler() {{
              svg.attr("transform", "translate(" + d3.event.translate + ") scale(" + d3.event.scale + ")");
          }}

          var links_g = svg.append("svg:g");

          var nodes_g = svg.append("svg:g");

          var x = d3.scale.linear()
                    .domain([0, {max_err}])
                    .range([1, 100])
                    .clamp(true);

          var brush = d3.svg.brush()
                        .y(x)
                        .extent([5, 5]);

          svg.append("svg:defs").selectAll("marker")
              .data(["end"])
              .enter().append("svg:marker")
              .attr("id", String)
              .attr("viewBox", "0 -5 10 10")
              .attr("refX", 15)
              .attr("refY", -1.5)
              .attr("markerWidth", 6)
              .attr("markerHeight", 6)
              .attr("orient", "auto")
              .append("svg:path")
              .attr("d", "M0,-5L10,0L0,5");

          var path = svg.append("svg:g")
                        .selectAll("path")
                        .data(force.links())
                        .enter().append("svg:path")
//                        .attr("class", function (d) {{
//                            return "link " + d.type;
//                        }})
                        .style("stroke",function (d,i) {{
                            return d.stroke;
                        }})
                        .attr("class", "link")
                        .attr("marker-end", "url(#end)")
                        //.style("stroke-width", function(d) {{ return (d.errors/{max_err})*5; }});

          var g = svg.append("svg:g")
              .attr("class", "x axis")
              .attr("transform", "translate(" + (w - 50)  + "," + (20) + ")")
              .call(d3.svg.axis()
                .scale(x)
                .orient("left")
                .tickFormat(function(d) {{ return d; }})
                .tickSize(0)
                .tickPadding(12))
            .select(".domain")
            .select(function() {{ return this.parentNode.appendChild(this.cloneNode(true)); }})
              .attr("class", "halo");

          svg.append("text")
             .attr("x", w - 15)
             .attr("y", 10)
             .attr("text-anchor", "end")
             .attr("font-size", "12px")
             .style("opacity", 0.5)
             .text("Number of Errors");

          var circle = svg.append("svg:g")
                          .selectAll("circle")
                          .data(force.nodes())
                          .enter().append("svg:circle")
                          .attr("r", 6)
                          .call(force.drag);

          var text = svg.append("svg:g")
                        .selectAll("g")
                        .data(force.nodes())
                        .enter().append("svg:g")
                        .attr("class", "nodeText");

          // A copy of the text with a thick white stroke for legibility.
          text.append("svg:text")
              .attr("x", 8)
              .attr("y", ".31em")
              .attr("class", "shadow")
              .text(function (d) {{
                  return d.name;
              }});

          text.append("svg:text")
              .attr("x", 8)
              .attr("y", ".31em")
              .text(function (d) {{
                  return d.name;
              }});

          var slider = svg.append("svg:g")
                          .attr("class", "slider")
                          .call(brush);

          slider.selectAll(".extent,.resize")
                .remove();

          var handle = slider.append("circle")
                             .attr("class", "handle")
                             .attr("transform", "translate(" + (w - 50) + "," + (20) + ")")
                             .attr("r", 6);

          brush.on("brush", brushed);

          slider.call(brush.extent([5, 5]))
                .call(brush.event);

          createTypeFilter();
          //svg.call(d3.behavior.zoom().on("zoom", zoomHandler));

          function tick() {{
              path.attr("d", function (d) {{
                  var dx = d.target.x - d.source.x,
                      dy = d.target.y - d.source.y,
                      dr = Math.sqrt(dx * dx + dy * dy);
                  return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0 1," + d.target.x + "," + d.target.y;
              }});

              circle.attr("transform", function (d) {{
                  return "translate(" + d.x + "," + d.y + ")";
              }});

              text.attr("transform", function (d) {{
                  return "translate(" + d.x + "," + d.y + ")";
              }});
          }}

          function createTypeFilter() {{
              d3.select(".filterContainer").selectAll("div")
                .data(["Danger", "Warning", "Good"])
                .enter()
                .append("div")
                .attr("class", "checkbox-container")
                .append("label")
                .each(function (d) {{
                      d3.select(this).append("input")
                        .attr("type", "checkbox")
                        .attr("id", function (d) {{
                            return "chk_" + d;
                         }})
                        .attr("checked", true)
                        .on("click", function (d, i) {{
                            // register on click event
                            var lVisibility = this.checked ? "visible" : "hidden";
                            if (d === 'Danger') danger = this.checked;
                            else if (d === 'Warning') warning = this.checked;
                            else if (d === 'Good') good = this.checked;
                            filterTypeGraph(d, lVisibility);
                         }});
                d3.select(this).append("span")
                  .text(function (d) {{
                      return d;
                  }});
              }});
              $("#sidebar").show();
          }}

          function filterTypeGraph(aType, aVisibility) {{
              var value = brush.extent()[0];

              if (d3.event.sourceEvent) {{
                value = x.invert(d3.mouse(this)[1]);
                brush.extent([value, value]);
              }}
              handle.attr("cy", x(value));
              var threshold = value;
              path.style("visibility", function (o) {{
                  var lOriginalVisibility = $(this).css("visibility");
                  return o.type === aType && o.value >= threshold ? aVisibility : lOriginalVisibility;
              }});

              circle.style("visibility", function (o, i) {{
                  var lHideNode = true;
                  path.each(function (d, i) {{
                      if ((d.source === o || d.target === o) && d.value >= threshold) {{
                          if ($(this).css("visibility") === "visible") {{
                              lHideNode = false;
                              d3.select(d3.selectAll(".nodeText")[0][i]).style("visibility", "visible");
                              return "visible";
                          }}
                      }}
                  }});
                  if (lHideNode) {{
                      d3.select(d3.selectAll(".nodeText")[0][i]).style("visibility", "hidden");
                      return "hidden";
                  }}
              }});
          }}

          function filterGraph(aValue) {{
              path.style("visibility", function (o) {{
                  if (o.type === 'Danger' && !danger) return "hidden";
                  if (o.type === 'Warning' && !warning) return "hidden";
                  if (o.type === 'Good' && !good) return "hidden";

                  return o.value >= aValue ? "visible" : "hidden";
              }});

              circle.style("visibility", function (o, i) {{
                  var lHideNode = true;
                  path.each(function (d, i) {{
                      if (d.source === o || d.target === o) {{
                         if ((!((d.type === 'Danger'  && !danger) ||
                                (d.type === 'Warning' && !warning) ||
                                (d.type === 'Good'    && !good))) &&
                             (($(this).css("visibility") === "visible"))) {{
                              lHideNode = false;
                              d3.select(d3.selectAll(".nodeText")[0][i]).style("visibility", "visible");
                              return "visible";
                          }}
                      }}
                  }});
                  if (lHideNode) {{
                      d3.select(d3.selectAll(".nodeText")[0][i]).style("visibility", "hidden");
                      return "hidden";
                  }}
              }});
          }}

      }});
    '''.format(data=data, max_err=max_err)

def pairwise_graph_html():
  return '''
    <div id="container" class="container">
      <div id="sidebar" style="display: none;">
        <div class="item-group">
            <label class="item-label">Filter</label>
            <div id="filterContainer" class="filterContainer checkbox-interaction-group"></div>
        </div>
      </div>
      <div id="graphContainer" class="graphContainer"></div>
    </div>
  '''


def generate_html_report(input_dir, prec_at_k, pairwise, class_distribution, class_accuracy, accuracy_coverage):
    return '''
      <!DOCTYPE html>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
      <script src="http://d3js.org/d3.v3.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.js"></script>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.15/c3.min.css">
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
      <style>
        .axis {{
          opacity: 0.5;
          font: 10px sans-serif;
          -webkit-user-select: none;
          -moz-user-select: none;
          user-select: none;
        }}
        .axis .domain {{
          fill: none;
          stroke: #000;
          stroke-opacity: .3;
          stroke-width: 4px;
          stroke-linecap: round;
        }}
        .axis .halo {{
            fill: none;
            stroke: #ddd;
            stroke-width: 3px;
            stroke-linecap: round;
        }}
        .slider .handle {{
            fill: #fff;
            stroke: #000;
            stroke-opacity: .5;
            stroke-width: 1.25px;
            cursor: grab;
        }}
        path.link {{
            fill: none;
            stroke: #666;
            stroke-width: 1.5px;
        }}
        circle {{
            fill: #ccc;
            stroke: #333;
            stroke-width: 1.5px;
        }}
        text {{
            font: 10px sans-serif;
            pointer-events: none;
        }}
        text.shadow {{
            stroke: #fff;
            stroke-width: 3px;
            stroke-opacity: .8;
        }}
        .graphContainer {{
            text-shadow: -1px -1px 0 white, 1px -1px 0 white, -1px 1px 0 white, 1px 1px 0 white;
        }}
        #sidebar {{
            position: absolute;
            z-index: 2;
            background-color: #FFF;
            padding: 10px;
            margin: 5px;
            border: 1px solid #6895b4;
            min-height: 3px;
            min-width: 8px;
        }}
      </style>
      <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
        <body>
          <div class="container">
            <h3>Experimental Analysis - {input_dir}</h3>

            <ul class="nav nav-tabs">
              <li class="active"><a data-toggle="tab" href="#home">Class Distribution</a></li>
              <li><a data-toggle="tab" href="#class_acc_tab">Class Accuracy</a></li>
              <li><a data-toggle="tab" href="#prec_at_k_tab">Precision @ K</a></li>
              <li><a data-toggle="tab" href="#pairwise_error_tab">Pairwise Class Error</a></li>
              <li><a data-toggle="tab" href="#accuracy_coverage_tab">Accuracy vs Coverage</a></li>
              <li><a data-toggle="tab" href="#pairwise_graph_tab">Pairwise Error Graph</a></li>
            </ul>

            <div class="tab-content">
              <div id="home" class="tab-pane fade in active">
                <h3>Dataset Summary</h3>
                <div id="class_distribution_pie"></div>
                <hr />
                <div id="class_distribution_plot"></div>
                <hr />
                {class_distribution_table}
              </div>
              <div id="class_acc_tab" class="tab-pane fade">
                <h3>Accuracy per Class Size</h3>
                <div id="class_accuracy_pie"></div>
                <hr />
                <div id="class_accuracy_plot"></div>
                <hr />
                {class_accuracy_table}
              </div>
              <div id="prec_at_k_tab" class="tab-pane fade">
                <h3>Precision @ K</h3>
                <div id="prec_at_k_plot"></div>
                <hr />
                {prec_at_k_table}
              </div>
              <div id="pairwise_error_tab" class="tab-pane fade">
                <h3>Pairwise Class Errors</h3>
                <div id="pairwise_pie"></div>
                <hr />
                {pairwise_table}
                {pairwise_examples}
              </div>
              <div id="accuracy_coverage_tab" class="tab-pane fade">
                <h3>Accuracy vs Coverage</h3>
                <div id="accuracy_coverage_plot"></div>
              </div>
              <div id="pairwise_graph_tab" class="tab-pane fade">
                {pairwise_graph_html}
              </div>
            </div>
          </div>

          <script type="text/javascript">
            {prec_at_k_script}
            {class_distribution_script}
            {class_accuracy_script}
            {pairwise_script}
            {pairwise_graph_script}
            {accuracy_coverage_script}
          </script>

        </body>
      </html>
    '''.format(input_dir=input_dir,
               prec_at_k_table=prec_at_k['table'], prec_at_k_script=prec_at_k['script'],
               pairwise_table=pairwise['table'], pairwise_examples=pairwise['examples'], pairwise_script=pairwise['script'],
               pairwise_graph_html=pairwise['graph-html'], pairwise_graph_script=pairwise['graph-script'],
               class_distribution_table=class_distribution['table'], class_distribution_script=class_distribution['script'],
               class_accuracy_table=class_accuracy['table'], class_accuracy_script=class_accuracy['script'], accuracy_coverage_script=accuracy_coverage['script'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Summarizes dataset.csv file (CSV) and a training workspace (JSON) producing number of questions, intents and entities')
    parser.add_argument('-i', '--input', nargs=1, help='K-Fold Cross Validation results folder (with test sets, predictions and precision_at_k files)')
    args = parser.parse_args()

    results, prec_at_k = parse(args.input[0]) # results is a list of (question, real_class, predicted_class, confidence), prec_at_k is the precision@K values
    dataset = class_stats(results)
    pairwise_err, examples = pairwise_errors(results)
    with open('{}/consolidated_report.html'.format(args.input[0]), 'w', encoding="UTF-8") as out_file:
        out_file.write(generate_html_report(args.input[0],
                               {'table': prec_at_k_table(prec_at_k), 'script': prec_at_k_script(prec_at_k)},
                               {'table': pairwise_table(pairwise_err), 'examples': pairwise_examples(pairwise_err, examples), 'script': pairwise_script(pairwise_err),
                                'graph-html': pairwise_graph_html(), 'graph-script': pairwise_graph_script(pairwise_err)},
                               {'table': class_distribution_table(dataset), 'script': class_distribution_script(dataset)},
                               {'table': class_accuracy_table(dataset), 'script': class_accuracy_script(dataset)},
                               {'script': accuracy_vs_coverage_script(accuracy_vs_coverage(results))}))

