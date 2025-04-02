/**
 * Simple logger utility for consistent frontend logging
 */

// Log levels
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

// Whether to enable debug logs
const DEBUG_MODE = import.meta.env.VITE_DEBUG === 'true';

/**
 * Formatted logger function
 * @param level Log level
 * @param component Component or module name
 * @param message Log message
 * @param data Optional data object
 */
function log(level: LogLevel, component: string, message: string, data?: any) {
  // Skip debug logs in production unless debug mode is enabled
  if (level === 'debug' && !DEBUG_MODE) {
    return;
  }

  const timestamp = new Date().toISOString();
  const prefix = `[${timestamp}] [${level.toUpperCase()}] [${component}]`;

  switch (level) {
    case 'debug':
      console.debug(prefix, message, data !== undefined ? data : '');
      break;
    case 'info':
      console.info(prefix, message, data !== undefined ? data : '');
      break;
    case 'warn':
      console.warn(prefix, message, data !== undefined ? data : '');
      break;
    case 'error':
      console.error(prefix, message, data !== undefined ? data : '');
      break;
  }
}

export default {
  debug: (component: string, message: string, data?: any) => log('debug', component, message, data),
  info: (component: string, message: string, data?: any) => log('info', component, message, data),
  warn: (component: string, message: string, data?: any) => log('warn', component, message, data),
  error: (component: string, message: string, data?: any) => log('error', component, message, data),
}; 