module.exports = {
  devServer: (devServerConfig) => {
    // Remove deprecated options to prevent warnings
    delete devServerConfig.onAfterSetupMiddleware;
    delete devServerConfig.onBeforeSetupMiddleware;
    
    // Use the new setupMiddlewares option
    devServerConfig.setupMiddlewares = (middlewares, devServer) => {
      return middlewares;
    };
    
    return devServerConfig;
  },
}