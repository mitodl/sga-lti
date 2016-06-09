var path = require("path");
var webpack = require('webpack');
var NodeNeat = require("node-neat");

module.exports = {
  context: __dirname,
  entry: {
    'root': './static/js/root',
    'style': './static/js/style',
  },
  output: {
    path: path.resolve('./static/bundles/'),
    filename: "[name].js"
  },

  module: {
    loaders: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        loader: "react-hot!babel-loader?presets[]=es2015&presets[]=react",
      },  // to transform JSX into JS
      {
        test: /\.scss$/,
        exclude: /node_modules/,
        loader: 'style!css!sass'
      }
    ]
  },

  sassLoader: {
    includePaths: NodeNeat.includePaths
  },

  resolve: {
    modulesDirectories: ['node_modules'],
    extensions: ['', '.js', '.jsx']
  },
  plugins: [
    new webpack.DefinePlugin({
      'process.env': {
        'NODE_ENV': '"development"'
      }
    })
  ],
  devtool: 'source-map'
};
